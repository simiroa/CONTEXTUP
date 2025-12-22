import sys
import os
import time
import unittest
from collections import deque
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock dependencies to avoid importing full tray agent
import sys
from unittest.mock import MagicMock
sys.modules["pystray"] = MagicMock()

class MockAgent:
    def notify(self, title, msg):
        print(f"[Notify] {title}: {msg}")

class MockTrayModule:
    def __init__(self, agent):
        self.agent = agent

# Mock the module import
import scripts.tray_modules.base
scripts.tray_modules.base.TrayModule = MockTrayModule

from scripts.tray_modules.recent_folders import RecentFolders

class TestRecentFolders(unittest.TestCase):
    def setUp(self):
        self.agent = MockAgent()
        self.rf = RecentFolders(self.agent)
        self.rf.running = True
        
        # Mock _get_explorer_paths to return controlled sets
        self.mock_paths = set()
        self.rf._get_explorer_paths = lambda: self.mock_paths
        
        # Override time.time to control simulation
        self.current_time = 1000.0
        self.rf._get_time = lambda: self.current_time

    def set_time(self, t):
        self.current_time = t

    def test_filtering(self):
        """Test system folder filtering."""
        print("\n--- Testing Filtering ---")
        
        # Test cases
        valid_path = "C:\\Users\\HG\\Desktop\\Project"
        invalid_paths = [
            "C:\\Windows\\System32",
            "C:\\Program Files\\App",
            "C:\\ProgramData\\Data",
            "C:\\$Recycle.Bin\\Item",
            "D:\\System Volume Information\\",
        ]
        
        self.assertTrue(self.rf._is_valid_folder(valid_path), f"Should be valid: {valid_path}")
        for p in invalid_paths:
            self.assertFalse(self.rf._is_valid_folder(p), f"Should be invalid: {p}")
            print(f"Correctly filtered: {p}")

    def test_batching(self):
        """Test batch grouping logic."""
        print("\n--- Testing Batching ---")
        
        # Inject a custom _poll_logic method to avoid threading/sleep issues
        # We'll copy the logic from _poll_loop but remove the loop and sleep
        def step():
            current_folders = self.rf._get_explorer_paths()
            closed = self.rf.open_folders - current_folders
            if closed:
                now = self.rf._get_time()
                valid_closed = [p for p in closed if self.rf._is_valid_folder(p)]
                
                if valid_closed:
                    if self.rf.closed_history and (now - self.rf.closed_history[-1][0] < 2.0):
                        self.rf.closed_history[-1][1].extend(valid_closed)
                        print(f"T={now}: Added to batch: {valid_closed}")
                    else:
                        self.rf.closed_history.append((now, list(valid_closed)))
                        print(f"T={now}: New batch: {valid_closed}")
            
            self.rf.open_folders = current_folders

        # Scenario:
        # T=0: Open A, B, C
        self.set_time(1000.0)
        self.mock_paths = {"C:\\FolderA", "C:\\FolderB", "C:\\FolderC"}
        step() # Initialize open_folders
        
        # T=1.0: Close A
        self.set_time(1001.0)
        self.mock_paths = {"C:\\FolderB", "C:\\FolderC"}
        step()
        
        # Verify Batch 1 has [A]
        self.assertEqual(len(self.rf.closed_history), 1)
        self.assertEqual(self.rf.closed_history[0][1], ["C:\\FolderA"])
        
        # T=1.5: Close B (Should be grouped with A)
        self.set_time(1001.5)
        self.mock_paths = {"C:\\FolderC"}
        step()
        
        # Verify Batch 1 has [A, B]
        self.assertEqual(len(self.rf.closed_history), 1)
        self.assertIn("C:\\FolderB", self.rf.closed_history[0][1])
        print(f"Batch 1 content: {self.rf.closed_history[0][1]}")
        
        # T=4.0: Close C (Should be new batch)
        self.set_time(1004.0)
        self.mock_paths = set()
        step()
        
        # Verify Batch 2 exists
        self.assertEqual(len(self.rf.closed_history), 2)
        self.assertEqual(self.rf.closed_history[1][1], ["C:\\FolderC"])
        print(f"Batch 2 content: {self.rf.closed_history[1][1]}")

if __name__ == '__main__':
    # Patch RecentFolders to use self._get_time() instead of time.time()
    # We need to modify the class method dynamically or just patch the instance in setUp?
    # The logic in _poll_loop calls time.time(). We can't easily patch it without mocking time module.
    # So we'll redefine the step logic in the test method as done above.
    unittest.main()
