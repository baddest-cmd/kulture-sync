import os
import json
from typing import Dict, Any, Optional

class StateManager:
    def __init__(self, session_id: str, db_client: Optional[Any] = None):
        self.session_id = session_id
        self.db_client = db_client
        self.is_gcp = db_client is not None or "GOOGLE_APPLICATION_CREDENTIALS" in os.environ
        self.local_cache_path = f"/tmp/kulture_sync_{session_id}.json"
        
        if self.is_gcp and not self.db_client:
            try:
                from google.cloud import firestore
                self.db_client = firestore.Client()
                print(f"[StateManager] Connected to GCP Firestore for session: {session_id}")
            except Exception as e:
                print(f"[StateManager] Firestore connection deferred: {e}. Using local cache.")
                self.is_gcp = False

        if not self.is_gcp:
            print(f"[StateManager] Offline mode: tracking state locally at {self.local_cache_path}")

    def get_state(self) -> Dict[str, Any]:
        if self.is_gcp:
            doc_ref = self.db_client.collection("kulture_sync_sessions").document(self.session_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return self._get_initial_state()
        else:
            if os.path.exists(self.local_cache_path):
                with open(self.local_cache_path, "r") as f:
                    return json.load(f)
            return self._get_initial_state()

    def update_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        state = self.get_state()
        for k, v in updates.items():
            if isinstance(v, dict) and k in state and isinstance(state[k], dict):
                state[k].update(v)
            else:
                state[k] = v
        
        if self.is_gcp:
            doc_ref = self.db_client.collection("kulture_sync_sessions").document(self.session_id)
            doc_ref.set(state, merge=True)
        else:
            with open(self.local_cache_path, "w") as f:
                json.dump(state, f, indent=4)
        return state

    def _get_initial_state(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": "INITIALISED",
            "last_processed_chunk": -1,
            "total_tracks": 0,
            "processed_tracks": [],
            "aligned_playlists": {},
            "network": {
                "connection_type": "UNKNOWN",
                "is_metered": True,
                "cellular_sync_override": False
            },
            "metrics": {
                "total_context_tax_saved": 0.0,
                "estimated_data_saved_mb": 0.0,
                "errors_logged": []
            }
        }
