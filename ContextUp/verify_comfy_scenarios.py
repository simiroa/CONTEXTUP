
import sys
import json
import random
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from manager.helpers.comfyui_client import ComfyUIManager

class ScenarioTester:
    def __init__(self):
        self.mgr = ComfyUIManager(port=8190)
        self.results = {}
        
    def log(self, name, status, msg=""):
        symbol = "✅" if status else "❌"
        print(f"{symbol} [{name}] {msg}")
        self.results[name] = status

    def run_all(self):
        print("=== Starting ComfyUI Scenario Verification ===")
        
        # 1. Connectivity
        if not self.test_connection(): return
        
        # 2. Model Fetching
        ckpt_name = self.test_model_fetching()
        if not ckpt_name:
            print("❌ Cannot proceed without a valid checkpoint.")
            return

        # 3. Basic Workflow (Efficiency Nodes)
        self.test_basic_gen(ckpt_name)
        
        # 4. Advanced Workflow (Impact Pack)
        self.test_advanced_gen(ckpt_name)
        
        self.print_summary()

    def test_connection(self):
        try:
            if self.mgr.is_running():
                self.log("Connectivity", True, f"Server found on port {self.mgr.active_port}")
                return True
            else:
                self.log("Connectivity", False, "Server not reachable")
                return False
        except Exception as e:
            self.log("Connectivity", False, str(e))
            return False

    def test_model_fetching(self):
        try:
            ckpts = self.mgr.get_input_options("CheckpointLoaderSimple", "ckpt_name")
            if ckpts:
                self.log("Fetch Checkpoints", True, f"Found {len(ckpts)} models. Using: {ckpts[0]}")
                return ckpts[0]
            else:
                self.log("Fetch Checkpoints", False, "No checkpoints returned from API.")
                return None
        except Exception as e:
            self.log("Fetch Checkpoints", False, str(e))
            return None

    def test_basic_gen(self, ckpt_name):
        print("\n--- Testing Basic Generation (Efficiency Nodes) ---")
        wf = self._build_workflow(ckpt_name, use_detailer=False)
        self._submit_workflow("Basic Generation", wf)

    def test_advanced_gen(self, ckpt_name):
        print("\n--- Testing Advanced Generation (Impact Pack) ---")
        wf = self._build_workflow(ckpt_name, use_detailer=True)
        self._submit_workflow("Advanced Generation", wf)

    def _submit_workflow(self, name, workflow):
        try:
            # We don't want to wait for full image generation, just validation that the prompt is accepted.
            # However, prompt rejection usually happens immediately.
            # Queue prompt
            res = self.mgr.queue_prompt(workflow)
            if 'prompt_id' in res:
                self.log(name, True, f"Accepted. ID: {res['prompt_id']}")
            else:
                self.log(name, False, f"Server rejected prompt: {res}")
        except urllib.error.HTTPError as e:
            # Parse ComfyUI error data
            err_msg = e.read().decode()
            self.log(name, False, f"HTTP {e.code}: {err_msg}")
        except Exception as e:
            self.log(name, False, f"Error: {e}")

    def _build_workflow(self, ckpt, use_detailer):
        # Miniaturized version of Creative Studio Advanced logic
        wf = {}
        
        # 1. Loader
        wf["1"] = {
            "class_type": "Efficient Loader",
            "inputs": {
                "ckpt_name": ckpt,
                "vae_name": "Baked VAE",
                "clip_skip": -1,
                "lora_name": "None",
                "lora_model_strength": 1.0,
                "lora_clip_strength": 1.0,
                "positive": "test run, 1girl",
                "negative": "low quality",
                "token_normalization": "none",
                "weight_interpretation": "comfy",
                "empty_latent_width": 512,
                "empty_latent_height": 512,
                "batch_size": 1
            }
        }
        
        # 2. Sampler
        wf["2"] = {
            "class_type": "KSampler (Efficient)",
            "inputs": {
                "seed": random.randint(0, 10000),
                "steps": 1, # FAST
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "preview_method": "auto",
                "vae_decode": "true",
                "model": ["1", 0],
                "positive": ["1", 1],
                "negative": ["1", 2],
                "latent_image": ["1", 3],
                "optional_vae": ["1", 4]
            }
        }
        
        final_out = ["2", 5]
        
        if use_detailer:
             # 3. Detector
            wf["3"] = {
                "class_type": "UltralyticsDetectorProvider",
                "inputs": { "model_name": "bbox/face_yolov8m.pt" }
            }
            # 4. Detailer
            wf["4"] = {
                "class_type": "FaceDetailer",
                "inputs": {
                    "guide_size": 256,
                    "guide_size_for": True,
                    "max_size": 768,
                    "seed": 0,
                    "steps": 1,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 0.1,
                    "feather": 5,
                    "noise_mask": True,
                    "force_inpaint": True,
                    "bbox_threshold": 0.5,
                    "bbox_dilation": 10,
                    "bbox_crop_factor": 3.0,
                    "sam_detection_hint": "center-1",
                    "spot_percent": 0.5,
                    "wildcard": "",
                    "cycle": 1,
                    
                    "image": final_out,
                    "model": ["1", 0],
                    "clip": ["1", 5], # Corrected from 4 ??
                    "vae": ["1", 4],
                    "positive": ["1", 1],
                    "negative": ["1", 2],
                    "bbox_detector": ["3", 0]
                }
            }
            final_out = ["4", 0]

        # 5. Save (Dummy)
        wf["10"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "Test/Scenarios",
                "images": final_out
            }
        }
        return wf

    def print_summary(self):
        print("\n=== Verification Summary ===")
        all_pass = True
        for name, status in self.results.items():
            if not status: all_pass = False
            r = "PASS" if status else "FAIL"
            print(f"{name:<25}: {r}")
        
        if all_pass:
            print("\n✅ All Scenarios Passed. The Advanced GUI should work properly.")
        else:
            print("\n❌ Issues Found. Check logs above.")

if __name__ == "__main__":
    tester = ScenarioTester()
    tester.run_all()
