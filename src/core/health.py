import sys
import platform
import subprocess
import importlib
import os
from pathlib import Path

# Add src to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.external_tools import get_ffmpeg
from core.settings import load_settings

class HealthCheck:
    def __init__(self):
        self.results = []
        self.settings = load_settings()

    def run_all(self):
        """Run all checks and return a list of (category, status, message) tuples."""
        self.results = []
        self.check_system()
        self.check_gpu()
        self.check_ffmpeg()
        self.check_dependencies() # System deps
        self.check_ai_env()       # Conda deps
        self.check_api()
        return self.results

    def _add_result(self, category, status, message):
        """
        status: "OK", "WARNING", "ERROR"
        """
        self.results.append((category, status, message))

    def check_system(self):
        try:
            info = f"{platform.system()} {platform.release()} ({platform.machine()})"
            self._add_result("System", "OK", f"OS: {info}")
            
            py_ver = sys.version.split()[0]
            self._add_result("System", "OK", f"Main Python: {py_ver}")
        except Exception as e:
            self._add_result("System", "ERROR", f"Failed to get system info: {e}")

    def check_gpu(self):
        try:
            import torch
            if torch.cuda.is_available():
                vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
                name = torch.cuda.get_device_name(0)
                self._add_result("GPU", "OK", f"CUDA Available: {name} ({vram:.1f} GB VRAM)")
            else:
                self._add_result("GPU", "WARNING", "CUDA not available (System). AI features might be slow.")
        except ImportError:
            self._add_result("GPU", "WARNING", "PyTorch not installed in System env (Normal for Dual-Env).")
        except Exception as e:
            self._add_result("GPU", "ERROR", f"GPU check failed: {e}")

    def check_ffmpeg(self):
        try:
            ffmpeg_path = get_ffmpeg()
            if ffmpeg_path == "ffmpeg":
                # Check if it's actually in path
                import shutil
                if not shutil.which("ffmpeg"):
                     self._add_result("FFmpeg", "ERROR", "FFmpeg not found in PATH or tools folder.")
                     return

            # Try execution
            result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self._add_result("FFmpeg", "OK", f"Found: {version_line}")
            else:
                self._add_result("FFmpeg", "ERROR", "FFmpeg found but failed to execute.")
        except Exception as e:
            self._add_result("FFmpeg", "ERROR", f"FFmpeg check failed: {e}")

    def check_dependencies(self):
        # System dependencies
        required = [
            ("cv2", "opencv-python"),
            ("PIL", "pillow"),
            ("google.genai", "google-genai"),
            ("ollama", "ollama"),
            ("piexif", "piexif"),
            ("faster_whisper", "faster-whisper")
        ]
        
        for module_name, pkg_name in required:
            try:
                importlib.import_module(module_name)
                self._add_result("System Deps", "OK", f"{pkg_name} installed.")
            except ImportError:
                self._add_result("System Deps", "ERROR", f"Missing: {pkg_name}")
            except Exception as e:
                self._add_result("System Deps", "WARNING", f"Error loading {pkg_name}: {e}")

    def check_ai_env(self):
        try:
            from utils.ai_runner import get_conda_env_info
            env_info = get_conda_env_info()
            python_exe = env_info.get('PYTHON_EXE')
            
            if not python_exe or not Path(python_exe).exists():
                self._add_result("AI Env", "ERROR", "Conda environment not found.")
                return

            self._add_result("AI Env", "OK", f"Found Conda Env: {env_info.get('CONDA_ENV_PATH')}")

            # Check packages in Conda env
            check_script = "import torch; import rembg; import basicsr; import gfpgan; print('AI_DEPS_OK')"
            
            result = subprocess.run(
                [python_exe, "-c", check_script],
                capture_output=True,
                text=True
            )
            
            if "AI_DEPS_OK" in result.stdout:
                self._add_result("AI Env", "OK", "AI Dependencies (PyTorch, rembg, etc.) verified.")
            else:
                self._add_result("AI Env", "ERROR", f"AI Dependencies missing.\nOutput: {result.stderr}")

        except Exception as e:
            self._add_result("AI Env", "WARNING", f"AI Environment check failed: {e}")

    def check_api(self):
        # Gemini
        key = self.settings.get("GEMINI_API_KEY")
        if key:
            self._add_result("API", "OK", "Gemini API Key configured.")
        else:
            self._add_result("API", "WARNING", "Gemini API Key missing. AI generation will fail.")
            
        # Ollama
        url = self.settings.get("OLLAMA_URL")
        if url:
             self._add_result("API", "OK", f"Ollama URL: {url}")
        else:
             self._add_result("API", "WARNING", "Ollama URL not configured.")
