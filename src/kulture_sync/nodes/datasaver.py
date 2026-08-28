from typing import Dict, Any
from kulture_sync.state.firestore import StateManager

class DataSaverNode:
    def __init__(self, state_manager: StateManager):
        self.state_mgr = state_manager

    def execute(self, network_state: Dict[str, Any]) -> Dict[str, Any]:
        state = self.state_mgr.get_state()
        sync_override = state.get("network", {}).get("cellular_sync_override", False)
        
        connection_type = network_state.get("connection_type", "UNKNOWN")
        is_metered = network_state.get("is_metered", True)
        
        print(f"[DataSaverNode] Connection: {connection_type} (Metered={is_metered}, SyncOverride={sync_override})")

        self.state_mgr.update_state({
            "network": {
                "connection_type": connection_type,
                "is_metered": is_metered,
                "cellular_sync_override": sync_override
            }
        })

        if is_metered and not sync_override:
            print("[DataSaverNode] Metered network and no override! Route to HITL Pause.")
            return {
                "action": "TRIGGER_HITL_PAUSE",
                "estimated_data_mb": len(state.get("raw_catalog", [])) * 5.0
            }
        
        print("[DataSaverNode] Safe connection or override in place. Proceeding to background sync.")
        return {
            "action": "PROCEED_SYNC",
            "estimated_data_mb": len(state.get("raw_catalog", [])) * 5.0
        }
