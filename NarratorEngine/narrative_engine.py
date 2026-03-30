import json
import os
import sys
import google.generativeai as genai

# Constraint: No emojis, no mdash

class NarrativeEngine:
    def __init__(self, graph_path):
        self.graph_path = graph_path
        self.graph_data = self._load_graph()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro-latest')
        else:
            self.model = None

    def _load_graph(self):
        with open(self.graph_path, 'r') as f:
            return json.load(f)

    def get_subgraph_for_event(self, target_event_type, target_year):
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]
        
        # Find the target event node
        target_node = None
        for node in nodes:
            if node.get("event_type") == target_event_type and node.get("timestep") == target_year:
                target_node = node
                break
        
        if not target_node:
            # Try finding by general type in that year
            for node in nodes:
                if target_event_type.lower() in node.get("label", "").lower() and node.get("timestep") == target_year:
                    target_node = node
                    break
        
        if not target_node:
            return []

        # Simple extraction: all ancestors of the target node
        # Since it is a small graph, we can find direct parents
        relevant_nodes = [target_node]
        target_id = target_node["id"]
        
        # Find parents
        for edge in edges:
            if edge["target"] == target_id:
                # Add parent
                parent_node = next((n for n in nodes if n["id"] == edge["source"]), None)
                if parent_node:
                    relevant_nodes.append(parent_node)
                    # Add grandparents
                    for edge2 in edges:
                        if edge2["target"] == parent_node["id"]:
                            grandparent = next((n for n in nodes if n["id"] == edge2["source"]), None)
                            if grandparent:
                                relevant_nodes.append(grandparent)

        return relevant_nodes

    def get_causal_trace(self, target_event_type, target_year):
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]
        
        # Find the target event node
        target_node = None
        for node in nodes:
            if (node.get("event_type") == target_event_type or target_event_type.lower() in node.get("label", "").lower()) and node.get("timestep") == target_year:
                target_node = node
                break
        
        if not target_node:
            return f"Trace Error: Node '{target_event_type}' at year {target_year} not found."

        trace_lines = []
        trace_lines.append(f"Trace for: {target_node['label']} (ID: {target_node['id']})")
        
        def trace_recursive(node_id, depth=0):
            prefix = "  " * (depth + 1) + "|-- "
            parents = [l["source"] for l in edges if l["target"] == node_id]
            for p_id in parents:
                p_node = next((n for n in nodes if n["id"] == p_id), None)
                if p_node:
                    trace_lines.append(f"{prefix}{p_node['label']} (ID: {p_node['id']})")
                    if depth < 3: # Limit depth
                        trace_recursive(p_id, depth + 1)

        trace_recursive(target_node["id"])
        return "\n".join(trace_lines)

    def query(self, user_question):
        if not self.model:
            return {
                "narrative": "Error: GOOGLE_API_KEY environment variable not set.",
                "citations": [],
                "confidence": 0.0
            }

        # Improved year extraction handling punctuation
        year = None
        import re
        match = re.search(r'\b(\d+)\b', user_question)
        if match:
            year = int(match.group(1))
        
        # Extract target event type (simple keyword matching for demo)
        target_event = "Population Collapse Event"
        if "bleaching" in user_question.lower() or "temp" in user_question.lower():
            target_event = "Thermal Stress Event"
        elif "acid" in user_question.lower() or "ph" in user_question.lower():
            target_event = "Acidification Event"

        evidence = self.get_subgraph_for_event(target_event, year)
        
        if not evidence:
            return {
                "narrative": f"No data found for the specified event in year {year}.",
                "citations": [],
                "confidence": 0.0
            }

        prompt = self._build_prompt(evidence, user_question)
        max_retries = 3
        for attempt in range(max_retries):
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            try:
                result = json.loads(response.text)
                narrative = result.get("narrative", "")
                
                # Strict Validation: check that every sentence has a [NODE:id]
                sentences = [s.strip() for s in narrative.split('.') if s.strip()]
                all_cited = True
                for s in sentences:
                    if "[NODE:" not in s:
                        all_cited = False
                        break
                
                if all_cited:
                    return result
                else:
                    print(f"Validation failed (Attempt {attempt+1}): Missing citations in narrative.")
                    # Reinforce prompt for retry
                    prompt += "\n\nCRITICAL REMINDER: EVERY SINGLE SENTENCE MUST HAVE A [NODE:id] CITATION."
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": f"Failed to parse AI response: {str(e)}", "raw": response.text}
        
        return {"error": "Failed to generate valid citation-heavy response after 3 attempts.", "last_result": result}

    def _build_prompt(self, evidence, query):
        evidence_json = json.dumps(evidence, indent=2)
        return f"""
ROLE: You are the Causal Narrator, an AI engine that provides evidence-based explanations of simulation outputs.

EVIDENCE BLOCK (JSON):
{evidence_json}

CONSTRAINTS:
1. You MUST ONLY explain events using the data nodes provided in the EVIDENCE BLOCK.
2. DO NOT use any external domain knowledge.
3. Every claim or sentence MUST include a citation in the format [NODE:id] where id is the ID of the node from the evidence.
4. If the evidence is insufficient to explain the cause, state clearly what is missing.
5. Do not use emojis.
6. Do not use the character (mdash).
7. Return the response in the following JSON format:
{{
  "narrative": "your explanation here with [NODE:id] citations",
  "citations": [{{ "node_id": "id", "reason": "why this node was used" }}],
  "confidence": 0.95
}}

QUERY:
{query}
"""

if __name__ == "__main__":
    engine = NarrativeEngine("CausalGraph.json")
    
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python narrative_engine.py \"Your question here\"")
        print("  python narrative_engine.py --trace \"Event Type\" Year")
        sys.exit(0)

    if args[0] == "--trace":
        if len(args) < 3:
            print("Error: --trace requires an event type and a year.")
            sys.exit(1)
        event_type = args[1]
        year = int(args[2])
        print(engine.get_causal_trace(event_type, year))
    else:
        user_query = " ".join(args)
        print(f"Querying: {user_query}")
        print(json.dumps(engine.query(user_query), indent=2))
