import os
import pandas as pd
from typing import Dict, Any, List, Optional
from kulture_sync.state.firestore import StateManager

class IngestionNode:
    def __init__(self, state_manager: StateManager, chunk_size: int = 5):
        self.state_mgr = state_manager
        self.chunk_size = chunk_size

    def _resolve_csv_path(self, csv_path: str) -> str:
        candidates = [
            csv_path,
            os.path.abspath(csv_path),
            os.path.join(os.getcwd(), csv_path),
            os.path.join(os.getcwd(), "kulture-sync", csv_path),
            os.path.join(os.path.dirname(__file__), "../../../", csv_path),
            os.path.join(os.path.dirname(__file__), "../../../data", os.path.basename(csv_path)),
            os.path.join("/app/kulture-sync", csv_path),
            os.path.join("/app/kulture-sync/data", os.path.basename(csv_path)),
            os.path.join("/app/data", os.path.basename(csv_path)),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        raise FileNotFoundError(
            f"Could not resolve CSV path '{csv_path}'. Checked candidates: {candidates}"
        )

    def execute(
        self,
        csv_path: Optional[str] = "data/mock_migrated_library.csv",
        raw_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        state = self.state_mgr.get_state()
        
        if state.get("status") in ["INGESTED", "ALIGNED", "COMPLETED", "PAUSED_ON_HITL"]:
            print(f"[IngestionNode] Dataset already ingested. Resuming from active cache.")
            raw_catalog = state.get("raw_catalog", [])
            chunks = [raw_catalog[i:i + self.chunk_size] for i in range(0, len(raw_catalog), self.chunk_size)]
            return {
                "status": "RESUMING",
                "total_tracks": state.get("total_tracks", 0),
                "chunks": chunks
            }

        try:
            if raw_tracks is not None and len(raw_tracks) > 0:
                tracks_list = raw_tracks
                total_tracks = len(tracks_list)
                print(f"[IngestionNode] Ingested {total_tracks} raw tracks from payload.")
            else:
                resolved_path = self._resolve_csv_path(csv_path or "data/mock_migrated_library.csv")
                df = pd.read_csv(resolved_path)
                total_tracks = len(df)
                tracks_list = df.to_dict(orient="records")
                print(f"[IngestionNode] Ingested {total_tracks} tracks from {resolved_path}.")
            
            self.state_mgr.update_state({
                "status": "INGESTED",
                "total_tracks": total_tracks,
                "raw_catalog": tracks_list
            })
            
            chunks = [tracks_list[i:i + self.chunk_size] for i in range(0, len(tracks_list), self.chunk_size)]
            return {
                "status": "SUCCESS",
                "total_tracks": total_tracks,
                "chunks": chunks
            }
        except Exception as e:
            self.state_mgr.update_state({
                "status": "FAILED",
                "metrics": {"errors_logged": [f"Ingestion failed: {str(e)}"]}
            })
            raise e
