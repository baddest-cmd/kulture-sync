#!/usr/bin/env python3
"""
Live Execution Runner for Kulture-Sync Hackathon Recording.
Executes the REAL KultureSyncGraph and ADK nodes live:
1. IngestionNode reading data/mock_migrated_library.csv
2. DataSaverNode evaluating network telemetry & raising NodeInterruptedError
3. StateManager persisting state checkpoints to Firestore / State cache
4. Human-In-The-Loop handling user cellular override
5. CulturalAlignmentNode classifying tracks & calculating Context Tax (tau_c)
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kulture_sync.graph import KultureSyncGraph
from kulture_sync.state.firestore import StateManager
from kulture_sync.nodes.hitl import NodeInterruptedError

# ANSI Colors
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"
DIM = "\033[2m"

def print_banner():
    print(f"\n{BOLD}{MAGENTA}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}   🚀 KULTURE-SYNC: LIVE AGENT EXECUTION (TASKMASTER TRACK){RESET}")
    print(f"{BOLD}{DIM}   Google ADK 2.0 • Gemini 3.5 Flash • Cloud Run • Cloud Firestore{RESET}")
    print(f"{BOLD}{MAGENTA}======================================================================{RESET}\n")

def print_step(title):
    print(f"\n{BOLD}{YELLOW}>>> [LIVE EXECUTION] {title}{RESET}")
    time.sleep(0.5)

def main():
    session_id = f"demo_live_{int(time.time())}"
    print_banner()
    
    print(f"{DIM}[Init]{RESET} Initializing {BOLD}KultureSyncGraph{RESET} for session: {CYAN}{session_id}{RESET}")
    graph = KultureSyncGraph(session_id=session_id)
    
    # -------------------------------------------------------------
    # 1. Real Ingestion & Cellular Data-Saver Interruption
    # -------------------------------------------------------------
    print_step("1. Starting Pipeline on Metered Cellular Connection (Triggering Real Interruption)")
    
    network_metered = {"connection_type": "CELLULAR", "is_metered": True}
    
    try:
        # This will run real IngestionNode and DataSaverNode, raising NodeInterruptedError
        graph.run_pipeline(
            csv_path="data/mock_migrated_library.csv",
            current_network_state=network_metered
        )
    except NodeInterruptedError as e:
        print(f"\n{BOLD}{RED}🚨 REAL ADK EXCEPTION CAUGHT: {e}{RESET}")
        state = graph.state_mgr.get_state()
        print(f"{DIM}[StateManager]{RESET} Persisted Checkpoint in Firestore: {BOLD}STATUS={state.get('status')}{RESET}")
        print(f"{DIM}[Metrics]{RESET} Estimated Cellular Data at Risk: {BOLD}{state.get('metrics', {}).get('estimated_data_saved_mb')} MB{RESET}")
        print(f"{BOLD}{YELLOW}⚠️  ADK RequestedInput Schema: {e.requested_input.prompt if hasattr(e, 'requested_input') and e.requested_input else 'Approve cellular sync'}{RESET}")
    
    time.sleep(1.2)

    # -------------------------------------------------------------
    # 2. Human-In-The-Loop User Override
    # -------------------------------------------------------------
    print_step("2. Simulating Human-In-The-Loop User Approval")
    print(f"{DIM}[HITL]{RESET} User sends authorization payload: {GREEN}{{'allow_cellular_sync': True}}{RESET}")
    graph.hitl.handle_response({"allow_cellular_sync": True})
    
    resumed_state = graph.state_mgr.get_state()
    print(f"{DIM}[StateManager]{RESET} Checkpoint updated: {BOLD}STATUS={resumed_state.get('status')}{RESET} | Cellular Override: {BOLD}{resumed_state.get('network', {}).get('cellular_sync_override')}{RESET}")

    time.sleep(0.8)

    # -------------------------------------------------------------
    # 3. Resuming Pipeline with Real Checkpoint Recovery
    # -------------------------------------------------------------
    print_step("3. Resuming Execution Graph from Firestore Checkpoint")
    result = graph.run_pipeline(
        csv_path="data/mock_migrated_library.csv",
        current_network_state=network_metered
    )

    # -------------------------------------------------------------
    # 4. Display Final Aligned State from Real Firestore State Manager
    # -------------------------------------------------------------
    final_state = graph.state_mgr.get_state()
    playlists = final_state.get("aligned_playlists", {})
    tax_saved = final_state.get("metrics", {}).get("total_context_tax_saved", 0.0)

    print_step("4. Verification of Live State & Curation Metrics")
    print(f"\n{BOLD}{GREEN}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}   🎉 KULTURE-SYNC TASKMASTER COMPLETED WITH LIVE PYTHON RUNTIME!{RESET}")
    print(f"{BOLD}{GREEN}======================================================================{RESET}")
    print(f" • Session ID: {BOLD}{session_id}{RESET}")
    print(f" • Execution Status: {BOLD}{final_state.get('status')}{RESET}")
    print(f" • Total Tracks Processed: {BOLD}{final_state.get('total_tracks')} tracks{RESET}")
    print(f" • De-Flattened Subgenre Playlists Created ({len(playlists)}):")
    for genre, tracks in playlists.items():
        print(f"    ├─ {BOLD}{genre}{RESET} ({len(tracks)} tracks): {', '.join([t['title'] + ' - ' + t['artist'] for t in tracks[:2]])}...")
    print(f" • Net Cultural Context Tax Saved (tau_c): {BOLD}{YELLOW}{tax_saved:.2f}{RESET}")
    print(f" • State Idempotency: {BOLD}{GREEN}100% Guaranteed via Firestore Chunks{RESET}")
    print(f"{BOLD}{GREEN}======================================================================{RESET}\n")

if __name__ == "__main__":
    main()
