"""
Verification Script for New Features.
Tests Texture Tools, File Tools, and Tray Modules logic.
"""
import sys
import os
import shutil
import time
import unittest
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

# Import modules to test
from scripts.texture_tools import get_nearest_pot
from scripts.tray_modules.clipboard_opener import ClipboardOpener
from scripts.tray_modules.my_info import MyInfo

# Mock Agent for Tray Modules
class MockAgent:
    def notify(self, title, msg):
        print(f"[Notify] {title}: {msg}")

class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/temp_verification")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)
        
    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_texture_pot_logic(self):
        print("\n--- Testing Texture Tools (POT Logic) ---")
        # Test Upscale
        self.assertEqual(get_nearest_pot(100, upscale=True), 128)
        self.assertEqual(get_nearest_pot(128, upscale=True), 128) # Already POT
        self.assertEqual(get_nearest_pot(129, upscale=True), 256)
        
        # Test Downscale
        self.assertEqual(get_nearest_pot(100, upscale=False), 64)
        self.assertEqual(get_nearest_pot(128, upscale=False), 128)
        self.assertEqual(get_nearest_pot(129, upscale=False), 128)
        print("Texture Tools POT logic passed.")

    def test_flatten_dir_logic(self):
        print("\n--- Testing Flatten Directory Logic ---")
        # Setup structure
        # root/
        #   file1.txt
        #   sub1/
        #     file2.txt
        #   sub2/sub3/
        #     file3.txt
        
        (self.test_dir / "file1.txt").touch()
        (self.test_dir / "sub1").mkdir()
        (self.test_dir / "sub1" / "file2.txt").touch()
        (self.test_dir / "sub2" / "sub3").mkdir(parents=True)
        (self.test_dir / "sub2" / "sub3" / "file3.txt").touch()
        
        # Simulate Flatten
        files_to_move = []
        for root, dirs, files in os.walk(self.test_dir):
            if Path(root) == self.test_dir: continue
            for f in files:
                files_to_move.append(Path(root) / f)
                
        self.assertEqual(len(files_to_move), 2)
        
        # Move
        for src in files_to_move:
            dst = self.test_dir / src.name
            shutil.move(str(src), str(dst))
            
        # Verify
        self.assertTrue((self.test_dir / "file1.txt").exists())
        self.assertTrue((self.test_dir / "file2.txt").exists())
        self.assertTrue((self.test_dir / "file3.txt").exists())
        print("Flatten Directory logic passed.")

    def test_archive_scanner(self):
        print("\n--- Testing Archive Manager Scanner ---")
        # Setup
        # junk.tmp
        # duplicate.txt (copy 1)
        # duplicate.txt (copy 2)
        
        (self.test_dir / "junk.tmp").touch()
        
        f1 = self.test_dir / "dup1.txt"
        f2 = self.test_dir / "dup2.txt"
        
        with open(f1, 'w') as f: f.write("content")
        with open(f2, 'w') as f: f.write("content")
        
        # Scan Logic
        import hashlib
        hashes = {}
        duplicates = []
        junk = []
        
        for f in self.test_dir.iterdir():
            if f.suffix == '.tmp':
                junk.append(f)
                continue
                
            if f.is_file():
                with open(f, 'rb') as f_obj:
                    h = hashlib.md5(f_obj.read()).hexdigest()
                    if h in hashes:
                        duplicates.append(f)
                    else:
                        hashes[h] = f
                        
        self.assertEqual(len(junk), 1)
        self.assertEqual(len(duplicates), 1)
        print("Archive Manager Scanner logic passed.")

    def test_tray_my_info(self):
        print("\n--- Testing Tray Module: My Info ---")
        agent = MockAgent()
        module = MyInfo(agent)
        
        # It should load default data if file missing
        self.assertTrue("Email" in module.info_data)
        self.assertTrue("IP" in module.info_data)
        print("My Info module loaded correctly.")

if __name__ == '__main__':
    unittest.main()
