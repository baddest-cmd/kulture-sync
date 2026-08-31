# KultureSync: Taskmaster Background Agent for Regional Music Curation

[![Track](https://img.shields.io/badge/Track-Taskmaster-8b5cf6?style=flat-square)](https://devpost.com)
[![Google ADK](https://img.shields.io/badge/Agent%20Engine-Google%20ADK%202.0-ff5e36?style=flat-square)](https://cloud.google.com)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash-06b6d4?style=flat-square)](https://ai.google.dev)
[![Cloud Run](https://img.shields.io/badge/Compute-Google%20Cloud%20Run-10b981?style=flat-square)](https://cloud.google.com/run)
[![Firestore](https://img.shields.io/badge/State-Google%20Cloud%20Firestore-f59e0b?style=flat-square)](https://cloud.google.com/firestore)

KultureSync is an asynchronous, graph-based Taskmaster background agent built with **Google ADK 2.0** and **Gemini 3.5 Flash** on **Google Cloud Run**. 

The agent operates as a decoupled background worker: it ingests raw music libraries, senses network telemetry, and de-flattens generic umbrella classifications (*"World Music"* or *"Afrobeats"*) into authentic South African subgenres (*Amapiano, Gqom, Lekompo, Bacardi, Motswako, and Maskandi*). On metered cellular connections, it safely interrupts execution to protect mobile data allowances.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    Client([User Client / Migration Utility]) -->|POST /sync (HTTP 202 ACCEPTED)| FastAPIGateway[FastAPI Gateway on Cloud Run]
    FastAPIGateway -->|Dispatches Background Task| ADKGraph[Google ADK 2.0 Graph Pipeline]
    
    subgraph ADKGraph [KultureSync Execution Graph]
        Ingestion[1. IngestionNode\nParse CSV into chunks] --> DataSaver{2. DataSaverNode\nInspect Network Telemetry}
        
        DataSaver -->|Metered Cellular & No Override| HITLPause[3. HumanInTheLoopNode\nRaise NodeInterruptedError]
        HITLPause -->|Save Checkpoint| Firestore[Cloud Firestore Ledger\nSTATUS: PAUSED_ON_HITL]
        
        DataSaver -->|Unmetered Wi-Fi or User Override| Alignment[4. CulturalAlignmentNode\nGemini 3.5 Flash + Pydantic Schema]
        Alignment -->|Atomic State Commits| FirestoreState[Cloud Firestore Ledger\nSTATUS: COMPLETED]
    end
    
    Client -.->|GET /session/:id| StateQuery[Fetch De-Flattened Playlists & Saved Context Tax]
```

---

## ⚡ Core Agentic Behaviours

1. **Decoupled Background Execution:** The client triggers a library sync and receives an immediate `202 ACCEPTED` handshake. The client is freed while the agent executes asynchronously in the background.
2. **Network-Aware Data-Saver Guard:** Before network-intensive steps, the `DataSaverNode` evaluates network conditions. If metered cellular data is detected, the graph natively raises an ADK `NodeInterruptedError` and pauses execution.
3. **Atomic State Checkpointing & Idempotency:** The `StateManager` commits progress to Cloud Firestore after every chunk. Interrupted jobs resume from the exact last chunk without duplicate processing or wasted LLM tokens.
4. **Ethnomusicological Reasoning:** The `CulturalAlignmentNode` leverages **Gemini 3.5 Flash** with schema-enforced structured outputs, backed by a deterministic fallback heuristic engine for offline reliability.

---

## 📐 Mathematical Formulation

### The Inversion Problem
Standard recommenders assume completed streams ($B = 1$) reflect unconstrained listener preference ($M$), ignoring how default playlist placements ($C$) act as confounders:
$$P(B \mid M, C) \neq P(B \mid M)$$

### Cultural Context Tax ($\tau_c$)
When users bypass flat defaults to find authentic local music, they incur an operational and financial friction:
$$\tau_c(u) = \sum_{i \in S_u} \Phi(i) \cdot \mathbb{I}(i \in G_{\text{local}}) - \gamma \sum_{j \in S_u} \Phi(j) \cdot \mathbb{I}(j \notin G_{\text{local}})$$

KultureSync calculates and records the net Context Tax saved across every aligned playlist.

### 📚 Research Foundation & Empirical Audit
KultureSync's agentic architecture builds directly on empirical field research analyzing algorithmic flattening across streaming platforms in South Africa ($N=152$ listeners across Johannesburg and Pretoria). 

For the underlying research paper, causal graphs, and socio-technical audit notebooks, explore the upstream research repository:
* 🔗 **[baddest-cmd/for-the-kulture (GitHub)](https://github.com/baddest-cmd/for-the-kulture)**

---

## 🚀 Judge Quickstart & Reproduction Guide

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/shailoh/kulture-sync.git
cd kulture-sync

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Generate mock library dataset (10 tracks)
python3 scripts/generate_mock_data.py
```

### 2. Run Automated Verification Tests
Verify network interruption, chunk idempotency, and state persistence:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🧪 Testing the Live Background Agent (Step-by-Step)

### Step 1: Start the Background Agent Service
Start the FastAPI server locally (default port 8080):

```bash
python3 -m kulture_sync.app
```

---

### Step 2: Test Metered Cellular Interruption (Data-Saver Flow)
Trigger a sync simulating a metered cellular connection:

```bash
curl -X POST http://127.0.0.1:8080/sync \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "judge_demo_session",
    "connection_type": "CELLULAR",
    "is_metered": true,
    "cellular_sync_override": false
  }'
```
*Expected response:* `{"status": "ACCEPTED", "session_id": "judge_demo_session"}`

Query the session state to verify the agent paused safely:

```bash
curl -s http://127.0.0.1:8080/session/judge_demo_session
```
*Expected state:* `"status": "PAUSED_ON_HITL"`, `"estimated_data_saved_mb": 50.0`.

---

### Step 3: Authorize Cellular Sync & Resume from Checkpoint
Simulate user approval by sending the override flag:

```bash
curl -X POST http://127.0.0.1:8080/sync \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "judge_demo_session",
    "connection_type": "CELLULAR",
    "is_metered": true,
    "cellular_sync_override": true
  }'
```

Query the final de-flattened library:

```bash
curl -s http://127.0.0.1:8080/session/judge_demo_session
```
*Expected state:* `"status": "COMPLETED"`, with aligned playlists (`Amapiano`, `Gqom`, `Lekompo`, `Bacardi`, `Maskandi`, `Motswako`) and calculated `total_context_tax_saved`.

---

### Step 4: View the Interactive Demo UI (Optional)
Open **`http://localhost:8080`** in your browser to view:
* Split-screen catalog comparison (Flattened vs. De-flattened).
* Interactive ADK architecture graph.
* Live agent execution console.

---

## ☁️ Google Cloud Deployment

Deploy the agent to **Google Cloud Run** with always-on CPU allocation to support asynchronous background execution:

```bash
./scripts/deploy.sh
```

### Key Deployment Flags:
* `--no-cpu-throttling`: Ensures CPU remains allocated for background processing loops after HTTP responses complete.
* `--min-instances 0`: Enables automatic scale-to-zero when idle ($0.00 idle cost).

---

## 📈 Scale Boundaries

* **Interactive Tier (under 500 tracks):** Real-time execution via Cloud Run, Gemini 3.5 Flash structured outputs, and atomic Firestore checkpoints.
* **Bulk Migration Tier (over 5,000 tracks):** Offloads large catalog imports to **Google Cloud Tasks** and the **Gemini Batch API** for asynchronous queueing and 50% lower token costs.
