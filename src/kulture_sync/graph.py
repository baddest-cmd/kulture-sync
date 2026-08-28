from typing import Dict, Any, List, Optional
from kulture_sync.state.firestore import StateManager
from kulture_sync.nodes.ingestion import IngestionNode
from kulture_sync.nodes.alignment import CulturalAlignmentNode
from kulture_sync.nodes.datasaver import DataSaverNode
from kulture_sync.nodes.hitl import HumanInTheLoopNode, NodeInterruptedError

class KultureSyncGraph:
    def __init__(self, session_id: str):
        self.state_mgr = StateManager(session_id)
        self.ingestion = IngestionNode(self.state_mgr)
        self.alignment = CulturalAlignmentNode(self.state_mgr)
        self.datasaver = DataSaverNode(self.state_mgr)
        self.hitl = HumanInTheLoopNode(self.state_mgr)

    def run_pipeline(
        self,
        csv_path: Optional[str] = "data/mock_migrated_library.csv",
        current_network_state: Optional[Dict[str, Any]] = None,
        raw_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        network_state = current_network_state or {"connection_type": "WIFI", "is_metered": False}
        print(f"\n--- [KultureSyncGraph] Initiating background sync pipeline for session: {self.state_mgr.session_id} ---")
        
        ingest_res = self.ingestion.execute(csv_path=csv_path, raw_tracks=raw_tracks)
        data_saver_res = self.datasaver.execute(network_state)
        
        if data_saver_res["action"] == "TRIGGER_HITL_PAUSE":
            self.hitl.execute(data_saver_res["estimated_data_mb"])
        
        state = self.state_mgr.get_state()
        chunks_to_process = ingest_res.get("chunks", [])
        
        total_chunks = len(chunks_to_process)
        print(f"[KultureSyncGraph] Ingested. {total_chunks} chunks queued for de-flattening.")

        for idx, chunk in enumerate(chunks_to_process):
            last_processed = self.state_mgr.get_state().get("last_processed_chunk", -1)
            if idx <= last_processed:
                print(f"[KultureSyncGraph] Skipping chunk {idx} (already processed and saved to state).")
                continue
                
            self.alignment.execute(chunk, idx)

        self.state_mgr.update_state({"status": "COMPLETED"})
        print(f"--- [KultureSyncGraph] Pipeline completed successfully for session {self.state_mgr.session_id} ---")
        
        final_state = self.state_mgr.get_state()
        return {
            "status": "COMPLETED",
            "session_id": self.state_mgr.session_id,
            "playlists_created": list(final_state["aligned_playlists"].keys()),
            "total_tracks_processed": final_state["total_tracks"],
            "context_tax_saved": final_state["metrics"]["total_context_tax_saved"]
        }
