# Causal Narrator

The Causal Narrator is an Explainable AI (XAI) middleware system designed to bridge the gap between complex ecological simulation logs and human understanding. It uses the Gemini API to generate grounded, traceable, and auditable narrative explanations for events within a simulation.

## System Architecture

The project is structured into three distinct layers:

1. **Layer 1: SimLog Extractor** (`SimLogExtractor/sim_log_extractor.py`):
   - Parses raw simulation data (CSV).
   - Normalizes units and detects critical events based on defined thresholds.
   - Outputs a structured intermediate format (`SimGraph.json`).

2. **Layer 2: Narrative Graph Builder** (`NarratorEngine/graph_builder.py`):
   - Consumes the processed logs and applies temporal precedence rules.
   - Integrates domain knowledge from `rules.yaml` to establish causal links.
   - Builds a directed causal graph (`CausalGraph.json`).

3. **Layer 3: AI Narrative Engine** (`NarratorEngine/narrative_engine.py`):
   - Accepts natural language queries.
   - Extracts relevant subgraphs as evidence.
   - Generates grounded explanations using Gemini 1.5 Flash.
   - **Hallucination Guard**: Enforces 100% citation coverage for every sentence in the output.

## Installation

Ensure you have Python 3.14+ installed. Install the required dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

### 1. Process Simulation Logs
First, generate the initial graph data from your raw logs:

```powershell
python SimLogExtractor/sim_log_extractor.py
python NarratorEngine/graph_builder.py
```

### 2. Configure API Key
Set your Google AI API Key:

```powershell
$env:GOOGLE_API_KEY = "YOUR_API_KEY"
```

### 3. Query the Engine
Ask a question about the simulation:

```powershell
python NarratorEngine/narrative_engine.py "Why did the coral population drop in year 8?"
```

### 4. Trace Causal Chains
Visualize the specific chain of events leading to a result:

```powershell
python NarratorEngine/narrative_engine.py --trace "Population Collapse Event" 8
```

## Constraints

- This project strictly avoids the use of emojis in all code and documentation.
- The use of the (mdash) character is prohibited throughout the project.
- Every claim made by the AI must be anchored to a data node via a [NODE:id] citation.
