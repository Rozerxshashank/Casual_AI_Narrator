import json
import yaml
import networkx as nx
import os

def build_causal_graph(sim_graph_path, rules_path, output_path):
    if not os.path.exists(sim_graph_path):
        print(f"Error: {sim_graph_path} not found.")
        return

    with open(sim_graph_path, 'r') as f:
        sim_data = json.load(f)

    with open(rules_path, 'r') as f:
        rules = yaml.safe_load(f)

    G = nx.DiGraph()

    # Add variable nodes
    for var in sim_data["variables"]:
        var_id = var["id"]
        for point in var["series"]:
            node_id = f"{var_id}_{point['timestep']}"
            G.add_node(node_id, 
                       type="variable", 
                       variable_id=var_id, 
                       timestep=point["timestep"], 
                       value=point["value"],
                       label=f"{var['name']} at Year {point['timestep']}")

            # Continuity edge (Temporal)
            if point["timestep"] > 0:
                prev_node = f"{var_id}_{point['timestep'] - 1}"
                if G.has_node(prev_node):
                    G.add_edge(prev_node, node_id, type="continuity", weight=1.0)

    # Add event nodes
    for event in sim_data["events"]:
        node_id = event["id"]
        G.add_node(node_id, 
                   type="event", 
                   event_type=event["type"], 
                   timestep=event["timestep"], 
                   variable_id=event["variable_id"],
                   label=f"{event['type']} (Year {event['timestep']})")
        
        # Link variable to event (Direct trigger)
        trigger_node = f"{event['variable_id']}_{event['timestep']}"
        if G.has_node(trigger_node):
            G.add_edge(trigger_node, node_id, type="trigger", weight=1.0)

    # Apply Domain Rules
    for rule in rules:
        cause_type = rule["cause"]
        effect_type = rule["effect"]
        weight = rule.get("confidence", 1.0)
        
        # Case 1: Event to Event
        # Case 2: Variable ID to Event
        # For simplicity, we search for matches in the graph
        
        for node in G.nodes(data=True):
            u_id = node[0]
            u_data = node[1]
            
            # Match cause
            is_cause = False
            if u_data["type"] == "event" and u_data["event_type"] == cause_type:
                is_cause = True
            elif u_data["type"] == "variable" and u_data["variable_id"] == cause_type:
                is_cause = True
                
            if is_cause:
                u_time = u_data["timestep"]
                # Look for effect in subsequent timesteps or same timestep
                for v_id, v_data in G.nodes(data=True):
                    is_effect = False
                    if v_data["type"] == "event" and v_data["event_type"] == effect_type:
                        is_effect = True
                    elif v_data["type"] == "variable" and v_data["variable_id"] == effect_type:
                        is_effect = True
                        
                    if is_effect:
                        v_time = v_data["timestep"]
                        # Cause must precede or equal effect time
                        if 0 <= (v_time - u_time) <= 1:
                            G.add_edge(u_id, v_id, type="causal", weight=weight, description=rule["description"])

    # Export graph
    graph_data = nx.node_link_data(G)
    with open(output_path, 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"Built causal graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

if __name__ == "__main__":
    build_causal_graph("SimGraph.json", "NarratorEngine/rules.yaml", "CausalGraph.json")
