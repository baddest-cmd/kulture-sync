from typing import Dict, Any, Optional
from kulture_sync.state.firestore import StateManager

try:
    from google.adk.errors import NodeInterruptedError
    from google.adk.types import RequestedInput
except ImportError:
    class NodeInterruptedError(BaseException):
        def __init__(self, message: str, requested_input: Optional[Any] = None):
            super().__init__(message)
            self.message = message
            self.requested_input = requested_input

    class RequestedInput:
        def __init__(self, key: str, prompt: str, schema: Optional[Dict[str, Any]] = None):
            self.key = key
            self.prompt = prompt
            self.schema = schema or {"type": "boolean"}

class HumanInTheLoopNode:
    def __init__(self, state_manager: StateManager):
        self.state_mgr = state_manager

    def execute(self, estimated_data_mb: float) -> None:
        state = self.state_mgr.get_state()
        sync_override = state.get("network", {}).get("cellular_sync_override", False)
        
        if sync_override:
            print("[HumanInTheLoopNode] Cellular sync override detected. Proceeding.")
            return

        estimated_cost_rand = (estimated_data_mb / 1000.0) * 100.0
        prompt_text = (
            f"Syncing your library ({estimated_data_mb:.1f}MB) over cellular "
            f"will cost approximately R{estimated_cost_rand:.2f}. Proceed anyway?"
        )
        
        print(f"[HumanInTheLoopNode] PAUSING WORKFLOW GRAPH: Raising NodeInterruptedError...")
        
        input_request = RequestedInput(
            key="allow_cellular_sync",
            prompt=prompt_text,
            schema={
                "type": "object",
                "properties": {
                    "allow_cellular_sync": {
                        "type": "boolean",
                        "description": "Approve cellular sync"
                    }
                },
                "required": ["allow_cellular_sync"]
            }
        )

        self.state_mgr.update_state({
            "status": "PAUSED_ON_HITL",
            "metrics": {
                "estimated_data_saved_mb": estimated_data_mb
            }
        })

        raise NodeInterruptedError(
            message="Data-Saver Triggered: Waiting for cellular sync authorization.",
            requested_input=input_request
        )

    def handle_response(self, user_response: Dict[str, Any]) -> Dict[str, Any]:
        allow_cellular = user_response.get("allow_cellular_sync", False)
        print(f"[HumanInTheLoopNode] User input received: {user_response}")
        
        if allow_cellular:
            print("[HumanInTheLoopNode] Cellular override enabled.")
            self.state_mgr.update_state({
                "status": "RESUMED",
                "network": {
                    "cellular_sync_override": True
                }
            })
            return {"status": "OVERRIDE_ENABLED"}
        
        print("[HumanInTheLoopNode] Cellular sync deferred.")
        self.state_mgr.update_state({
            "status": "DEFERRED",
            "network": {
                "cellular_sync_override": False
            }
        })
        return {"status": "DEFERRED"}
