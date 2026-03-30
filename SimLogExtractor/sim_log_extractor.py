import csv
import json
import os

def extract_logs(input_csv, output_json):
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return

    variables = {
        "Temperature": {"id": "v_temp", "name": "Sea Surface Temperature", "unit": "Celsius", "series": []},
        "pH": {"id": "v_ph", "name": "Oceanic pH", "unit": "pH", "series": []},
        "CoralPopulation": {"id": "v_coral", "name": "Coral Population", "unit": "Percentage", "series": []}
    }
    
    events = []
    
    with open(input_csv, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestep = int(row["Year"])
            temp = float(row["Temperature"])
            ph = float(row["pH"])
            coral = float(row["CoralPopulation"])
            
            variables["Temperature"]["series"].append({"timestep": timestep, "value": temp})
            variables["pH"]["series"].append({"timestep": timestep, "value": ph})
            variables["CoralPopulation"]["series"].append({"timestep": timestep, "value": coral})
            
            # Event Detection
            if temp > 30.0:
                events.append({
                    "id": f"event_temp_{timestep}",
                    "type": "Thermal Stress Event",
                    "timestep": timestep,
                    "variable_id": "v_temp",
                    "trigger_value": temp,
                    "threshold": 30.0
                })
            
            if ph < 7.85:
                events.append({
                    "id": f"event_ph_{timestep}",
                    "type": "Acidification Event",
                    "timestep": timestep,
                    "variable_id": "v_ph",
                    "trigger_value": ph,
                    "threshold": 7.85
                })
                
            if coral < 50.0:
                events.append({
                    "id": f"event_coral_{timestep}",
                    "type": "Population Collapse Event",
                    "timestep": timestep,
                    "variable_id": "v_coral",
                    "trigger_value": coral,
                    "threshold": 50.0
                })

    sim_graph = {
        "metadata": {
            "run_id": "SIM-2026-001",
            "scenario": "Coral Reef Survival",
            "engine_version": "1.0",
            "start_year": 0,
            "end_year": 10
        },
        "variables": list(variables.values()),
        "events": events,
        "data_gaps": []
    }
    
    with open(output_json, 'w') as f:
        json.dump(sim_graph, f, indent=2)
    
    print(f"Extracted {len(events)} events to {output_json}")

if __name__ == "__main__":
    extract_logs("data/simulation_logs.csv", "SimGraph.json")
