import unittest
import os
import pandas as pd
from kulture_sync.graph import KultureSyncGraph
from kulture_sync.nodes.hitl import NodeInterruptedError
from kulture_sync.nodes.alignment import CulturalAlignmentNode

class TestKultureSyncPipeline(unittest.TestCase):
    def setUp(self):
        self.csv_path = "data/mock_migrated_library.csv"

    def tearDown(self):
        for s in ["test_cellular", "test_idempotency", "test_unmetered", "test_replay"]:
            if os.path.exists(f"/tmp/kulture_sync_{s}.json"):
                os.remove(f"/tmp/kulture_sync_{s}.json")

    def test_cellular_data_gate_interrupts_natively(self):
        """Verifies that on a metered connection, the graph interrupts execution to protect users."""
        session_id = "test_cellular"
        graph = KultureSyncGraph(session_id)
        mock_cellular = {"connection_type": "CELLULAR", "is_metered": True}
        
        with self.assertRaises(NodeInterruptedError):
            graph.run_pipeline(self.csv_path, mock_cellular)
            
        state = graph.state_mgr.get_state()
        self.assertEqual(state["status"], "PAUSED_ON_HITL")

    def test_unmetered_connection_runs_to_completion(self):
        """Verifies that on free Wi-Fi, the graph runs seamlessly to completion without prompts."""
        session_id = "test_unmetered"
        graph = KultureSyncGraph(session_id)
        mock_wifi = {"connection_type": "WIFI", "is_metered": False}
        
        result = graph.run_pipeline(self.csv_path, mock_wifi)
        
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("Amapiano", result["playlists_created"])
        self.assertIn("Lekompo", result["playlists_created"])

    def test_idempotent_state_recovery_after_failure(self):
        """Verifies that state-persistence protects against duplications (The Idempotency Trap)."""
        session_id = "test_idempotency"
        graph = KultureSyncGraph(session_id)
        mock_wifi = {"connection_type": "WIFI", "is_metered": False}
        
        df = pd.read_csv(self.csv_path)
        tracks_list = df.to_dict(orient="records")
        
        # Seed state simulating chunk 0 already completed
        graph.state_mgr.update_state({
            "status": "INGESTED",
            "total_tracks": len(tracks_list),
            "raw_catalog": tracks_list,
            "last_processed_chunk": 0,
            "aligned_playlists": {
                "Amapiano": [{"track_id": "T001", "title": "Sgudi Snyc", "aligned_genre": "Amapiano"}]
            }
        })
        
        result = graph.run_pipeline(self.csv_path, mock_wifi)
        self.assertEqual(result["status"], "COMPLETED")
        
        state = graph.state_mgr.get_state()
        self.assertEqual(state["last_processed_chunk"], 1)

    def test_chunk_replay_does_not_duplicate_tracks(self):
        """Verifies that executing the same chunk twice produces strictly deduplicated playlists."""
        session_id = "test_replay"
        graph = KultureSyncGraph(session_id)
        alignment_node = CulturalAlignmentNode(graph.state_mgr)

        sample_chunk = [
            {"track_id": "T100", "title": "Ke Star", "artist": "Focalistic", "genre": "Amapiano", "is_local": True, "popularity": 0.8},
            {"track_id": "T101", "title": "Gqom 5", "artist": "DJ Lag", "genre": "Gqom", "is_local": True, "popularity": 0.7}
        ]

        # Execute chunk first time
        alignment_node.execute(sample_chunk, chunk_idx=0)
        state_first = graph.state_mgr.get_state()
        amapiano_count_1 = len(state_first["aligned_playlists"].get("Amapiano", []))
        tax_1 = state_first["metrics"]["total_context_tax_saved"]

        # Replay the exact same chunk
        alignment_node.execute(sample_chunk, chunk_idx=0)
        state_second = graph.state_mgr.get_state()
        amapiano_count_2 = len(state_second["aligned_playlists"].get("Amapiano", []))
        tax_2 = state_second["metrics"]["total_context_tax_saved"]

        # Ensure no track duplication or double tax calculation occurred
        self.assertEqual(amapiano_count_1, amapiano_count_2)
        self.assertEqual(tax_1, tax_2)


if __name__ == "__main__":
    unittest.main()
