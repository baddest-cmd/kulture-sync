# KultureSync taskmaster agent

KultureSync is an asynchronous, graph-based background agent built with Google ADK 2.0 and Gemini 3.5 Flash on Cloud Run. The agent classifies South African music into local subgenres (such as Amapiano, Gqom, Lekompo, Bacardi, Motswako, and Maskandi) instead of broad umbrella tags. It also pauses execution on metered connections to reduce cellular data costs.

## Key features

* Firestore checkpoints: Saves progress so interrupted library sync jobs resume without reprocessing tracks or re-downloading data.
* Data-saver pause: Detects metered connections and raises an ADK `NodeInterruptedError`. The job resumes when the user approves cellular usage or reconnects to Wi-Fi.
* Classification audit: Quantifies algorithmic flattening by calculating the Context Tax ($\tau_c$) saved through local curation.

## Local quickstart

1. Activate the environment and install dependencies:
   ```bash
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Run the mock data generator:
   ```bash
   python3 scripts/generate_mock_data.py
   ```

3. Run the automated test suite:
   ```bash
   PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
   ```

## Cloud Run deployment

Deploy the service with always-on CPU allocation to support background execution:
```bash
./scripts/deploy.sh
```

## Scale boundaries

* Interactive tier (under 500 tracks): Processes requests in real time using structured outputs and Firestore checkpointing.
* Bulk migration tier (over 5,000 tracks): Offloads large library imports to Google Cloud Tasks and the Gemini Batch API for asynchronous processing at lower token cost.
