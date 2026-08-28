import os
import uvicorn
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from kulture_sync.graph import KultureSyncGraph
from kulture_sync.state.firestore import StateManager

app = FastAPI(title="KultureSync Taskmaster Background Agent")

class SyncRequest(BaseModel):
    session_id: str
    csv_path: Optional[str] = "data/mock_migrated_library.csv"
    raw_tracks: Optional[List[Dict[str, Any]]] = None
    tracks: Optional[List[Dict[str, Any]]] = None
    connection_type: str = "WIFI"
    is_metered: bool = False
    cellular_sync_override: bool = False

def run_graph_background(
    session_id: str,
    csv_path: Optional[str],
    connection_type: str,
    is_metered: bool,
    raw_tracks: Optional[List[Dict[str, Any]]] = None,
    cellular_sync_override: bool = False
):
    try:
        graph = KultureSyncGraph(session_id)
        if cellular_sync_override:
            graph.state_mgr.update_state({
                "network": {"cellular_sync_override": True}
            })
        graph.run_pipeline(
            csv_path=csv_path,
            current_network_state={"connection_type": connection_type, "is_metered": is_metered},
            raw_tracks=raw_tracks
        )
    except Exception as e:
        print(f"[App] Background pipeline failed: {e}")

@app.get("/")
def read_root():
    return {"status": "ACTIVE", "agent": "KultureSync Taskmaster Background Agent"}

@app.get("/session/{session_id}")
def get_session_state(session_id: str):
    mgr = StateManager(session_id)
    return mgr.get_state()

@app.post("/sync")
def trigger_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    tracks_payload = request.tracks if request.tracks is not None else request.raw_tracks
    background_tasks.add_task(
        run_graph_background,
        request.session_id,
        request.csv_path,
        request.connection_type,
        request.is_metered,
        tracks_payload,
        request.cellular_sync_override
    )
    return {
        "status": "ACCEPTED",
        "message": f"Sync pipeline initiated for session {request.session_id}",
        "session_id": request.session_id
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
