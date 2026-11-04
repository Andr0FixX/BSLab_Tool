import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import MagicMock
from core.cloud_sync import CloudSyncManager

class TestCloudSync(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock()
        self.sync_mgr = CloudSyncManager(logger=self.mock_logger)

    def test_local_database_stats(self):
        stats = self.sync_mgr.get_local_database_stats()
        self.assertIn("brands_count", stats)
        self.assertIn("total_models", stats)
        self.assertIn("mtk_preloaders", stats)
        self.assertIn("qualcomm_loaders", stats)

        self.assertGreaterEqual(stats["brands_count"], 10)
        self.assertGreaterEqual(stats["mtk_preloaders"], 800)
        self.assertGreaterEqual(stats["qualcomm_loaders"], 800)

    def test_check_for_updates_offline_fallback(self):
        # Point to unreachable URL to test offline fallback
        res = self.sync_mgr.check_for_updates(endpoint_url="http://127.0.0.1:59999/nonexistent_manifest.json")
        self.assertEqual(res["status"], "offline_verified")
        self.assertFalse(res["update_available"])
        self.assertIn("local_stats", res)

if __name__ == "__main__":
    unittest.main()
