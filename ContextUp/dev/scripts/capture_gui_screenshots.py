"""
GUI Screenshot Automation Tool (Enhanced with Logging & Safety)
================================================================

Captures screenshots of all ContextUp GUIs with comprehensive error detection,
file-based logging, checkpoint/resume functionality, and resource monitoring.

Features:
- File-based detailed logging (survives reboots)
- Checkpoint/Resume functionality
- System resource monitoring (memory, CPU)
- Enhanced process cleanup (prevents zombie processes)
- Worker process isolation (one GUI crash won't affect others)
- Multi-theme/language testing (Dark/En, Light/Ko)

Usage:
    python capture_gui_screenshots.py              # Capture all (default config)
    python capture_gui_screenshots.py --resume     # Resume from checkpoint
    python capture_gui_screenshots.py manager      # Capture specific
    python capture_gui_screenshots.py --list       # List available GUIs
    python capture_gui_screenshots.py --verbose    # Detailed console output
    python capture_gui_screenshots.py --themes     # Run Dark/En + Light/Ko cycles
"""

import subprocess
import sys
import time
import tempfile
import shutil
import json
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Enable DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Paths - script is in ContextUp/dev/scripts/
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # ContextUp/
SRC_DIR = PROJECT_ROOT / "src"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_ROOT = PROJECT_ROOT / "docs" / "gui_screenshots"
REPORT_DIR = SCRIPT_DIR / "test_reports"
TEMP_DIR = Path(tempfile.gettempdir()) / "contextup_test_files"
SETTINGS_PATH = CONFIG_DIR / "settings.json"

# Use ContextUp's embedded Python
EMBEDDED_PYTHON = PROJECT_ROOT / "tools" / "python" / "python.exe"
if not EMBEDDED_PYTHON.exists():
    print(f"[ERROR] Embedded Python not found: {EMBEDDED_PYTHON}")
    print(f"[ERROR] Please run install.bat first to setup Python environment")
    EMBEDDED_PYTHON = Path(sys.executable)  # Fallback to system Python

# Create directories
OUTPUT_ROOT.mkdir(exist_ok=True, parents=True)
REPORT_DIR.mkdir(exist_ok=True, parents=True)
TEMP_DIR.mkdir(exist_ok=True)

def _read_current_language():
    """Read current language setting from settings.json."""
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get("LANGUAGE", "en")
    except:
        return "en"

# Package GUIs that need python -m execution
PACKAGE_GUIS = {
    "finder": "features.finder.ui",
    "gemini_tools": "features.ai.standalone.gemini_img_tools.gui",
    "prompt_master": "features.prompt_master.main"
}

# GUIs that are slower to load
SLOW_GUIS = ["pdf_ocr", "marigold", "mesh_lod", "doc_convert"]

# GUI definitions: (id, script_path, (en_titles, ko_titles), file_type, extra_args)
# NOTE: Many GUIs don't have fully localized window titles, so ko_titles often include English fallbacks
GUI_LIST = [
    # Manager
    ("manager", "manager/main.py", (["ContextUp", "Manager"], ["ContextUp", "Manager"]), "none", []),
    
    # Image
    ("image_convert", "features/image/convert_gui.py", (["Image", "Convert"], ["Image", "Convert", "이미지"]), "image", []),
    ("image_compare", "features/image/compare_gui.py", (["Image", "Compare"], ["Image", "Compare", "비교"]), "image", ["--demo"]),
    ("merge_exr", "features/image/merge_exr.py", (["EXR", "Merge"], ["EXR", "Merge"]), "image", []),
    ("split_exr", "features/image/split_exr.py", (["EXR", "Split"], ["EXR", "Split"]), "exr", []),
    ("resize", "features/image/resize_gui.py", (["Resize", "Image"], ["Resize", "Image", "이미지"]), "image", []),
    ("packer", "features/image/packer_gui.py", (["Packer", "Texture", "ORM"], ["Packer", "ORM", "텍스처"]), "folder", ["--demo"]),
    ("image_split", "features/image/split_image.py", (["Split", "Channel"], ["Split", "Channel"]), "image", []),
    ("normal_roughness", "features/image/normal.py", (["Normal", "Roughness"], ["Normal", "Roughness"]), "image", []),
    ("texture_tools", "features/image/texture.py", (["Texture", "Tools"], ["Texture", "Tools"]), "image", []),
    ("upscale", "features/image/upscale.py", (["Upscale", "Image"], ["Upscale", "Image"]), "image", []),
    
    # Video
    ("video_convert", "features/video/convert_gui.py", (["Video", "Convert"], ["Video", "Convert", "영상"]), "video", []),
    ("video_audio", "features/video/audio_gui.py", (["Audio", "Tools"], ["Audio", "Tool", "오디오"]), "video", []),
    ("downloader", "features/video/downloader_gui.py", (["Downloader", "Video"], ["Downloader", "다운로더"]), "none", []),
    ("sequence_video", "features/video/seq_gui.py", (["Sequence", "Video"], ["Sequence", "Video", "시퀀스"]), "folder", []),
    ("to_video", "features/sequence/to_video_gui.py", (["Sequence", "Video"], ["Sequence", "Video"]), "sequence", []),
    ("analyze_seq", "features/sequence/analyze_gui.py", (["Sequence", "Analyze"], ["Sequence", "Analyze"]), "sequence", []),
    ("interpolation", "features/video/interpolation_gui.py", (["Interpolation", "Frame"], ["Interpolation", "Frame", "프레임"]), "video", []),
    
    # Audio
    ("audio_convert", "features/audio/convert_gui.py", (["Audio", "Convert"], ["Audio", "Convert", "오디오"]), "audio", []),
    ("audio_separate", "features/audio/separate_gui.py", (["Audio", "Separate"], ["Audio", "Separate", "분리"]), "none", ["--demo"]),
    
    # AI / ComfyUI
    ("marigold", "features/ai/marigold_gui.py", (["PBR", "Marigold"], ["PBR", "Marigold"]), "image", []),
    ("gemini_tools", "features/ai/standalone/gemini_img_tools/gui.py", (["Gemini", "AI"], ["Gemini", "AI"]), "image", []),
    ("creative_studio_z", "features/comfyui/creative_studio_z_gui.py", (["Creative", "Studio"], ["Creative", "Studio"]), "none", []),
    ("creative_studio_adv", "features/comfyui/creative_studio_advanced_gui.py", (["Creative", "Advanced"], ["Creative", "Advanced"]), "none", []),
    ("seedvr2", "features/comfyui/seedvr2_gui.py", (["SeedVR2"], ["SeedVR2"]), "none", []),
    ("ace_audio", "features/comfyui/ace_audio_edit_gui.py", (["ACE", "Audio"], ["ACE", "Audio"]), "none", []),
    ("icon_gen", "features/comfyui/icon_gen_gui.py", (["Icon", "Gen"], ["Icon", "Gen"]), "none", []),
    ("z_image_turbo", "features/comfyui/z_image_turbo_gui.py", (["Image", "Turbo"], ["Image", "Turbo"]), "none", []),
    ("noise_master", "features/image/noise_master_gui.py", (["Noise", "Master"], ["Noise", "Master"]), "none", []),
    
    # Mesh
    ("mesh_lod", "features/mesh/lod_gui.py", (["LOD", "Auto"], ["LOD", "Auto"]), "none", ["--demo"]),
    ("blender_bake", "features/mesh/bake_gui.py", (["Remesh", "Bake"], ["Remesh", "Bake", "리메쉬"]), "mesh", []),
    ("mesh_convert", "features/mesh/blender.py", (["Mesh", "Convert"], ["Mesh", "Convert"]), "mesh", ["convert"]),
    ("mesh_optimize", "features/mesh/blender.py", (["Mesh", "Optimize"], ["Mesh", "Optimize"]), "mesh", ["optimize"]),
    ("cad_convert", "features/mesh/mayo.py", (["CAD", "Mayo"], ["CAD", "Mayo"]), "mesh", []),
    
    # Document
    ("doc_convert", "features/document/convert_gui.py", (["Document", "Converter"], ["Document", "Converter", "문서"]), "pdf", ["--dev"]),
    
    # System
    ("rename", "features/system/rename.py", (["Rename", "Batch"], ["이름 바꾸기", "Rename"]), "folder", ["rename"]),
    ("renumber", "features/system/rename.py", (["Renumber", "Sequence"], ["Renumber", "Sequence"]), "folder", ["renumber"]),
    ("unwrap", "features/system/unwrap_folder_gui.py", (["Unwrap", "Folder"], ["폴더 풀기", "Unwrap"]), "folder", []),
    ("open_recent", "features/system/open_recent.py", (["Recent", "Open"], ["Recent", "Open"]), "none", []),
    ("metadata_tag", "features/system/metadata.py", (["Tagging", "Metadata"], ["Tagging", "Metadata"]), "image", []),
    
    # Finder / Prompt Master / AI Tools
    ("finder", "features/finder/ui.py", (["Finder", "Search"], ["Finder", "파인더"]), "folder", []),
    ("prompt_master", "features/prompt_master/main.py", (["Prompt", "Master"], ["Prompt", "Master", "프롬프트"]), "none", []),
    ("ai_text_lab", "features/tools/ai_text_lab.py", (["AI", "Red", "Lab", "Text"], ["AI", "Red", "Lab", "연구소"]), "none", []),
    
    # Leave Manager
    ("leave_manager", "features/leave_manager/gui.py", (["Leave", "Manager", "휴가"], ["Leave", "Manager", "휴가"]), "none", []),
]


# Resize map for GUIs that need more space (width, height)
RESIZE_MAP = {
    "blender_bake": (900, 950),
    "doc_convert": (900, 950),
    "marigold": (900, 950),
    "image_convert": (900, 950),
    "creative_studio_z": (1360, 900),
    "creative_studio_adv": (1380, 950),

    "ace_audio": (1200, 800),
    "image_compare": (1100, 800),
}


class ResourceMonitor:
    """Monitor and log system resource usage."""
    
    def __init__(self, logger):
        self.logger = logger
        self.has_psutil = HAS_PSUTIL
        
        if not self.has_psutil:
            logger.warning("psutil not installed - resource monitoring disabled")
            logger.warning("Install with: pip install psutil")
    
    def log_system_stats(self, prefix="SYSTEM"):
        """Log current system resource usage."""
        if not self.has_psutil:
            return
        
        try:
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            self.logger.info(
                f"{prefix} | CPU: {cpu:5.1f}% | Memory: {mem.percent:5.1f}% "
                f"({mem.used//1024//1024:,}MB / {mem.total//1024//1024:,}MB)"
            )
        except Exception as e:
            self.logger.debug(f"Failed to log system stats: {e}")
    
    def check_memory_warning(self, threshold=85):
        """Check if memory usage exceeds threshold."""
        if not self.has_psutil:
            return False
        
        try:
            mem = psutil.virtual_memory()
            if mem.percent > threshold:
                self.logger.warning(
                    f"⚠️ High memory usage: {mem.percent:.1f}% "
                    f"({mem.used//1024//1024:,}MB / {mem.total//1024//1024:,}MB)"
                )
                return True
        except Exception:
            pass
        
        return False
    
    def kill_process_tree(self, pid):
        """Kill a process and all its children."""
        if not self.has_psutil:
            return
        
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    self.logger.debug(f"Killing child process: {child.pid}")
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Kill parent
            try:
                self.logger.debug(f"Killing parent process: {parent.pid}")
                parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.debug(f"Process {pid} already terminated or access denied: {e}")


class CheckpointManager:
    """Manage test progress checkpoints for resume functionality."""
    
    def __init__(self, checkpoint_file: Path):
        self.file = checkpoint_file
        self.data = self.load()
    
    def load(self) -> Dict:
        """Load checkpoint data from file."""
        if self.file.exists():
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "session_id": None,
            "started_at": None,
            "completed": [],
            "failed": [],
            "skipped": [],
            "last_updated": None
        }
    
    def save(self):
        """Save checkpoint data to file."""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Failed to save checkpoint: {e}")
    
    def start_session(self, session_id: str):
        """Start a new test session."""
        self.data["session_id"] = session_id
        self.data["started_at"] = datetime.now().isoformat()
        self.save()
    
    def mark_completed(self, gui_id: str):
        """Mark a GUI test as completed."""
        if gui_id not in self.data["completed"]:
            self.data["completed"].append(gui_id)
        self.save()
    
    def mark_failed(self, gui_id: str):
        """Mark a GUI test as failed."""
        if gui_id not in self.data["failed"]:
            self.data["failed"].append(gui_id)
        self.save()
    
    def mark_skipped(self, gui_id: str):
        """Mark a GUI test as skipped."""
        if gui_id not in self.data["skipped"]:
            self.data["skipped"].append(gui_id)
        self.save()
    
    def is_completed(self, gui_id: str) -> bool:
        """Check if a GUI test was already completed."""
        return gui_id in self.data["completed"]
    
    def reset(self):
        """Reset checkpoint data."""
        self.data = {
            "session_id": None,
            "started_at": None,
            "completed": [],
            "failed": [],
            "skipped": [],
            "last_updated": None
        }
        self.save()


class TestResult:
    """Comprehensive test result with detailed error info."""
    
    def __init__(self, gui_id: str):
        self.gui_id = gui_id
        self.script_exists = False
        self.import_ok = False
        self.import_error = None
        self.launch_ok = False
        self.launch_error = None
        self.process_stderr = None
        self.process_returncode = None
        self.window_found = False
        self.screenshot_saved = False
        self.screenshot_path = None
        self.duration = 0.0
        self.timestamp = datetime.now().isoformat()
    
    @property
    def passed(self):
        return self.script_exists and self.import_ok and self.window_found
    
    @property
    def status(self):
        if not self.script_exists:
            return "SKIP"
        if not self.import_ok:
            return "IMPORT_FAIL"
        if not self.window_found:
            return "WINDOW_FAIL"
        if self.screenshot_saved:
            return "PASS"
        return "PARTIAL"
    
    def to_dict(self) -> Dict:
        return {
            "gui_id": self.gui_id,
            "status": self.status,
            "script_exists": self.script_exists,
            "import_ok": self.import_ok,
            "import_error": self.import_error,
            "launch_ok": self.launch_ok,
            "launch_error": self.launch_error,
            "functional_status": getattr(self, "functional_status", "UNKNOWN"),
            "localization_status": getattr(self, "localization_status", "UNKNOWN"),
            "memory_usage": getattr(self, "memory_usage", "N/A"),
            "process_stderr": self.process_stderr,
            "window_found": self.window_found,
            "screenshot_saved": self.screenshot_saved,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "duration": self.duration,
            "timestamp": self.timestamp,
        }


def setup_logging(session_id: str, verbose: bool = False) -> Tuple[logging.Logger, Path]:
    """Setup file-based logging system."""
    
    # Create log directories
    log_dir = REPORT_DIR / "gui_logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Master log file
    master_log_path = REPORT_DIR / f"test_{session_id}.log"
    
    # Setup master logger
    logger = logging.getLogger("ScreenshotTest")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    # File handler (rotating, max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        master_log_path,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info("=" * 70)
    logger.info(f"GUI Screenshot Test Session: {session_id}")
    logger.info(f"Log file: {master_log_path}")
    logger.info("=" * 70)
    
    return logger, master_log_path


def create_gui_logger(gui_id: str, session_id: str) -> logging.Logger:
    """Create a separate logger for each GUI test."""
    
    log_dir = REPORT_DIR / "gui_logs"
    log_path = log_dir / f"{gui_id}_{session_id}.log"
    
    gui_logger = logging.getLogger(f"GUI.{gui_id}")
    gui_logger.setLevel(logging.DEBUG)
    gui_logger.handlers.clear()
    gui_logger.propagate = False  # Don't propagate to parent
    
    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    gui_logger.addHandler(handler)
    
    return gui_logger


@contextmanager
def settings_context(updates: Dict[str, Any], logger):
    """Safely modify settings.json and restore it afterwards."""
    backup = None
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            
            # Apply updates
            new_settings = backup.copy()
            new_settings.update(updates)
            
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=4, ensure_ascii=False)
            logger.info(f"CONFIG | Applied settings: {updates}")
        else:
            logger.warning("CONFIG | settings.json not found, skipping config injection")
            
        yield
        
    finally:
        # Restore backup
        if backup:
            try:
                with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(backup, f, indent=4, ensure_ascii=False)
                logger.info("CONFIG | Restored original settings")
            except Exception as e:
                logger.error(f"CONFIG | Failed to restore settings: {e}")


def create_test_files(logger) -> Dict[str, str]:
    """Create dummy test files for GUI testing."""
    files = {}
    
    logger.info(f"SETUP | Creating test files in: {TEMP_DIR}")
    
    # Image
    if HAS_PIL:
        img_path = TEMP_DIR / "test_image.png"
        if not img_path.exists():
            img = Image.new('RGB', (512, 512), color='#4A90D9')
            img.save(img_path)
            logger.debug(f"SETUP | Created: {img_path.name}")
        files['image'] = str(img_path)
    else:
        files['image'] = None
        logger.warning("SETUP | PIL not available, image tests may fail")
    
    # EXR (fake)
    exr_path = TEMP_DIR / "test.exr"
    if not exr_path.exists():
        exr_path.write_text("FAKE EXR")
        logger.debug(f"SETUP | Created: {exr_path.name}")
    files['exr'] = str(exr_path)
    
    # Video (fake)
    vid_path = TEMP_DIR / "test_video.mp4"
    if not vid_path.exists():
        vid_path.write_bytes(b"FAKE VIDEO" * 100)
        logger.debug(f"SETUP | Created: {vid_path.name}")
    files['video'] = str(vid_path)
    
    # Audio (fake)
    aud_path = TEMP_DIR / "test_audio.mp3"
    if not aud_path.exists():
        aud_path.write_bytes(b"FAKE AUDIO" * 100)
        logger.debug(f"SETUP | Created: {aud_path.name}")
    files['audio'] = str(aud_path)
    
    # PDF (fake)
    pdf_path = TEMP_DIR / "test_doc.pdf"
    if not pdf_path.exists():
         pdf_path.write_bytes(b"%PDF-1.4 FAKE PDF CONTENT")
         logger.debug(f"SETUP | Created: {pdf_path.name}")
    files['pdf'] = str(pdf_path)

    # Mesh
    obj_path = TEMP_DIR / "test.obj"
    if not obj_path.exists():
        obj_path.write_text("v 0 0 0\\nv 1 0 0\\nv 1 1 0\\nf 1 2 3")
        logger.debug(f"SETUP | Created: {obj_path.name}")
    files['mesh'] = str(obj_path)
    
    # Sequence Folder
    seq_dir = TEMP_DIR / "test_sequence"
    seq_dir.mkdir(exist_ok=True)
    for i in range(1, 6):
         p = seq_dir / f"frame_{i:04d}.jpg"
         if not p.exists() and HAS_PIL:
             img = Image.new('RGB', (100, 100), color=(i*40 % 255, 0, 0))
             img.save(p)
         elif not p.exists():
             p.write_bytes(b"FAKE JPG")
    files['sequence'] = str(seq_dir)

    files['folder'] = str(TEMP_DIR)
    files['none'] = None
    
    logger.info(f"SETUP | Test files ready")
    return files


def find_window_flexible(title_keywords: List[str], logger, wait_time: float = 15.0, process_pid: int = None) -> Optional[Any]:
    """Find window matching any of the keywords, with flexible matching.
    
    Also includes fallback detection for BaseWindow-based GUIs that show as 'CTk'
    due to overrideredirect(True) hiding the title bar.
    """
    if not HAS_PYGETWINDOW:
        logger.error("WINDOW | pygetwindow not available")
        return None
    
    start = time.time()
    checked_titles = set()
    
    # Get initial window list to detect new windows
    try:
        initial_windows = set(gw.getAllTitles())
    except:
        initial_windows = set()
    
    while time.time() - start < wait_time:
        try:
            all_windows = gw.getAllTitles()
            
            for win_title in all_windows:
                if not win_title.strip():
                    continue
                
                # Exclude system windows
                if win_title == "Program Manager":
                    continue
                
                # Check if any keyword matches
                win_lower = win_title.lower()
                for keyword in title_keywords:
                    if keyword.lower() in win_lower:
                        windows = gw.getWindowsWithTitle(win_title)
                        if windows:
                            win = windows[0]
                            if win.width > 100 and win.height > 100:  # Valid window
                                if win_title not in checked_titles:
                                    logger.info(f"WINDOW | Found: '{win_title}' ({win.width}x{win.height})")
                                    checked_titles.add(win_title)
                                return win
            
            # Fallback: Check for 'CTk' windows (BaseWindow with custom title bar)
            # Only use if keywords didn't match anything after some time
            if time.time() - start > 3.0:  # After 3 seconds, try CTk fallback
                for win_title in all_windows:
                    # Match 'CTk' or windows that weren't in initial list
                    if win_title == 'CTk' or (win_title not in initial_windows and win_title.strip()):
                        windows = gw.getWindowsWithTitle(win_title)
                        if windows:
                            win = windows[0]
                            if win.width > 100 and win.height > 100:
                                if win_title not in checked_titles:
                                    logger.info(f"WINDOW | Found (CTk fallback): '{win_title}' ({win.width}x{win.height})")
                                    checked_titles.add(win_title)
                                return win
                                
        except Exception as e:
            logger.debug(f"WINDOW | Error during search: {e}")
        
        time.sleep(0.5)
    
    logger.warning(f"WINDOW | Not found after {wait_time}s (keywords: {title_keywords})")
    try:
        visible = [t for t in gw.getAllTitles() if t.strip()]
        logger.debug(f"WINDOW | Visible windows: {visible}")
    except:
        pass
    return None


def capture_window_screenshot(window, output_path: Path, logger) -> bool:
    """Capture screenshot of a specific window."""
    if not HAS_PIL:
        logger.error("SCREENSHOT | PIL not available")
        return False
    
    try:
        window.activate()
        time.sleep(0.8)  # Wait for window to come to front
    except Exception as e:
        logger.debug(f"SCREENSHOT | Failed to activate window: {e}")
    
    try:
        x, y, w, h = window.left, window.top, window.width, window.height
        # Adjust for negative coordinates (multi-monitor)
        x = max(0, x)
        y = max(0, y)
        
        bbox = (x, y, x + w, y + h)
        screenshot = ImageGrab.grab(bbox)
        screenshot.save(output_path)
        logger.info(f"SCREENSHOT | Saved: {output_path.name} ({w}x{h})")
        return True
    except Exception as e:
        logger.error(f"SCREENSHOT | Failed: {e}")
        logger.debug(traceback.format_exc())
        return False



def run_gui_test(
    gui_id: str, 
    script_path: str, 
    title_configs: Tuple[List[str], List[str]], 
    file_type: str, 
    extra_args: List[str], 
    test_files: Dict, 
    output_dir: Path,
    logger: logging.Logger,
    resource_monitor: ResourceMonitor,
    is_korean: bool = False,
    dev_mode: bool = False
) -> TestResult:
    """Run comprehensive GUI test with detailed logging."""
    
    # Create GUI-specific logger
    gui_logger = create_gui_logger(gui_id, datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    result = TestResult(gui_id)
    start_time = time.time()
    
    logger.info(f"")
    logger.info(f"{'='*70}")
    logger.info(f"TEST START | {gui_id}")
    logger.info(f"{'='*70}")
    
    gui_logger.info(f"GUI Test: {gui_id}")
    gui_logger.info(f"Script: {script_path}")
    gui_logger.info(f"Language Mode: {'Korean' if is_korean else 'English'}")
    
    # Log system resources before test
    resource_monitor.log_system_stats(f"{gui_id} | PRE-TEST")
    
    full_script = SRC_DIR / script_path
    
    # Check script exists
    result.script_exists = full_script.exists()
    if not result.script_exists:
        logger.warning(f"SKIP | Script not found: {script_path}")
        gui_logger.warning(f"Script not found: {full_script}")
        result.duration = time.time() - start_time
        return result
    
    gui_logger.info(f"Script exists: {full_script}")
    
    # Build command - check if package GUI
    if gui_id in PACKAGE_GUIS:
        module_path = PACKAGE_GUIS[gui_id]
        gui_logger.info(f"Using package import: {module_path}")
        cmd = [str(EMBEDDED_PYTHON), "-m", module_path]
    else:
        cmd = [str(EMBEDDED_PYTHON), str(full_script)]
    
    cmd.extend(extra_args)
    
    test_file = test_files.get(file_type)
    if test_file:
        cmd.append(test_file)
        gui_logger.info(f"Test file: {test_file}")
    
    gui_logger.info(f"Command: {' '.join(cmd)}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Developer mode: show all input parameters
    if dev_mode:
        logger.info(f"[DEV] GUI ID: {gui_id}")
        logger.info(f"[DEV] Script: {script_path}")
        logger.info(f"[DEV] File Type: {file_type}")
        logger.info(f"[DEV] Extra Args: {extra_args}")
        logger.info(f"[DEV] Test File: {test_file}")
        logger.info(f"[DEV] Full Command: {' '.join(cmd)}")
        logger.info(f"[DEV] CWD: {PROJECT_ROOT}")
        logger.info(f"[DEV] PYTHONPATH: {env.get('PYTHONPATH', 'N/A')}")
        if not test_file and file_type != 'none':
            logger.warning(f"[DEV] ⚠️  No test file for type '{file_type}' - GUI may fail to start!")

    # DEBUG: Verify settings.json content before launch
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
                logger.info(f"DEBUG | Settings on disk - THEME: {current_settings.get('THEME')}, LANG: {current_settings.get('LANGUAGE')}")
    except Exception as e:
        logger.warning(f"DEBUG | Failed to read settings.json: {e}")

    # Launch GUI
    proc = None
    try:
        logger.info(f"LAUNCH | Starting GUI subprocess...")
        gui_logger.info("Launching subprocess...")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # creationflags=0x08000000,  # CREATE_NO_WINDOW for console
            cwd=str(PROJECT_ROOT),
            env=env
        )
        result.launch_ok = True
        gui_logger.info(f"Process started: PID={proc.pid}")
        logger.debug(f"LAUNCH | Process PID: {proc.pid}")
        
        # Give it time to start
        time.sleep(2.0)
        
        # Check if process crashed immediately
        retcode = proc.poll()
        if retcode is not None:
            result.process_returncode = retcode
            _, stderr = proc.communicate(timeout=2)
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            result.process_stderr = stderr_text[:1000]
            
            gui_logger.error(f"Process exited immediately with code {retcode}")
            if stderr_text:
                gui_logger.error(f"STDERR:\n{stderr_text}")
            
            if retcode != 0:
                logger.error(f"FAIL | Process exited with code {retcode}")
                if result.process_stderr:
                    logger.error(f"STDERR | {result.process_stderr[:200]}")
                result.duration = time.time() - start_time
                return result
        
        # Find window
        en_titles, ko_titles = title_configs
        search_titles = ko_titles if is_korean else en_titles
        logger.info(f"WINDOW | Searching for window (keywords: {search_titles})...")
        gui_logger.info(f"Searching for window with keywords: {search_titles}")
        
        # Adjust wait time for slow GUIs
        wait_time = 18.0 if gui_id in SLOW_GUIS else 12.0
        window = find_window_flexible(search_titles, gui_logger, wait_time=wait_time)
        
        if window:
            result.window_found = True
            result.import_ok = True  # Window found implies successful import/launch
            
            # --- Resize Window if needed ---
            if gui_id in RESIZE_MAP:
                target_w, target_h = RESIZE_MAP[gui_id]
                gui_logger.info(f"Resizing window to {target_w}x{target_h}")
                try:
                    window.resizeTo(target_w, target_h)
                    time.sleep(1.0) # Allow resize/repaint
                except Exception as e:
                    gui_logger.warning(f"Failed to resize window: {e}")

            logger.info(f"SUCCESS | Window found: {window.title}")
            gui_logger.info(f"Window found: {window.title}")
            
            # --- Localization Check ---
            result.localization_status = "PASS"
            # Strict(er) check: ensure matching entry actually looks right
            # We already matched by keyword but let's be explicit
            matches = [t for t in search_titles if t.lower() in window.title.lower()]
            if not matches:
                 # Should theoretically not happen if find_window_flexible works, but good to double check logic
                 result.localization_status = "FAIL"
                 gui_logger.warning(f"LOCALIZATION | Matches not found in title '{window.title}' vs {search_titles}")
            else:
                 gui_logger.info(f"LOCALIZATION | Verified matches: {matches}")

            # --- Functional Status Check ---
            # If we got here, window exists so process is running and GUI is visible
            result.functional_status = "STABLE"
            
            # Record resources
            try:
                if HAS_PSUTIL and proc and proc.pid:
                    p = psutil.Process(proc.pid)
                    mem_info = p.memory_info()
                    result.memory_usage = f"{mem_info.rss / 1024 / 1024:.1f} MB"
                    gui_logger.info(f"RESOURCE | Memory: {result.memory_usage}")
            except:
                result.memory_usage = "Unknown"

            # Capture screenshot
            output_file = output_dir / f"{gui_id}.png"
            
            # Delete existing file to prevent overwrite issues
            if output_file.exists():
                try:
                    output_file.unlink()
                    gui_logger.info(f"Deleted existing screenshot: {output_file.name}")
                except Exception as e:
                    gui_logger.warning(f"Failed to delete existing file: {e}")
            
            gui_logger.info(f"Capturing screenshot to: {output_file}")
            
            if capture_window_screenshot(window, output_file, gui_logger):
                result.screenshot_saved = True
                result.screenshot_path = output_file
                logger.info(f"SUCCESS | Screenshot saved")
            else:
                logger.warning(f"PARTIAL | Window found but screenshot failed")
            
            # Close window
            try:
                gui_logger.info("Closing window...")
                window.close()
                time.sleep(0.3)
            except Exception as e:
                gui_logger.warning(f"Failed to close window: {e}")
        else:
            logger.error(f"FAIL | Window not found")
            gui_logger.error("Window not found after timeout")
            result.functional_status = "CRASHED/TIMEOUT"
            result.localization_status = "N/A"
            if result.process_returncode is not None:
                result.functional_status = f"EXITED({result.process_returncode})"
            
    except Exception as e:
        result.launch_error = str(e)
        logger.error(f"ERROR | {e}")
        gui_logger.error(f"Exception during test: {e}")
        gui_logger.error(traceback.format_exc())
    
    finally:
        # Enhanced process cleanup
        if proc and proc.poll() is None:
            gui_logger.info("Terminating process...")
            logger.debug(f"CLEANUP | Terminating PID {proc.pid}")
            
            try:
                # First try graceful termination
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                    gui_logger.info("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful fails
                    gui_logger.warning("Process didn't terminate, killing...")
                    logger.debug(f"CLEANUP | Force killing PID {proc.pid}")
                    
                    # Use resource monitor to kill process tree
                    resource_monitor.kill_process_tree(proc.pid)
                    
                    try:
                        proc.kill()
                        proc.wait(timeout=2)
                        gui_logger.info("Process killed")
                    except:
                        gui_logger.error("Failed to kill process")
            except Exception as e:
                gui_logger.error(f"Error during cleanup: {e}")
                logger.debug(f"CLEANUP | Error: {e}")
        
        # Log system resources after test
        resource_monitor.log_system_stats(f"{gui_id} | POST-TEST")
        resource_monitor.check_memory_warning()
    
    result.duration = time.time() - start_time
    logger.info(f"COMPLETE | Status: {result.status} | Duration: {result.duration:.1f}s")
    gui_logger.info(f"Test completed: {result.status} in {result.duration:.1f}s")
    
    return result


def print_summary(results: List[TestResult], logger):
    """Print human-readable summary."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = [r for r in results if r.status == "PASS"]
    partial = [r for r in results if r.status == "PARTIAL"]
    failed = [r for r in results if r.status in ("IMPORT_FAIL", "WINDOW_FAIL", "SKIP")]
    
    logger.info(f"")
    logger.info(f"Total:   {len(results)}")
    logger.info(f"  ✓ Passed:  {len(passed)}")
    logger.info(f"  ~ Partial: {len(partial)}")
    logger.info(f"  ✗ Failed:  {len(failed)}")
    
    if failed:
        logger.info("")
        logger.info("FAILURES:")
        for r in failed:
            logger.info(f"  - {r.gui_id} ({r.status})")
            if r.launch_error:
                logger.info(f"    Launch Error: {r.launch_error}")
            if r.process_stderr:
                logger.info(f"    Stderr: {r.process_stderr[:100]}...")
    
    logger.info("=" * 70)


def save_json_report(results: List[TestResult], report_path: Path, logger):
    """Save detailed JSON report."""
    report_data = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r.status == "PASS"),
        "failed": sum(1 for r in results if r.status in ("IMPORT_FAIL", "WINDOW_FAIL")),
        "skipped": sum(1 for r in results if r.status == "SKIP"),
        "failed_localization": sum(1 for r in results if getattr(r, "localization_status", "UNKNOWN") == "FAIL"),
        "crashed": sum(1 for r in results if "CRASHED" in getattr(r, "functional_status", "UNKNOWN")),
        "results": [r.to_dict() for r in results]
    }
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"REPORT | JSON saved: {report_path}")
    except Exception as e:
        logger.error(f"REPORT | Failed to save JSON: {e}")


def run_test_suite(
    config_name: str, 
    settings_update: Dict, 
    test_files: Dict, 
    gui_filter: str = None,
    logger: logging.Logger = None,
    checkpoint_mgr: CheckpointManager = None,
    resource_monitor: ResourceMonitor = None,
    resume: bool = False,
    dev_mode: bool = False
) -> List[TestResult]:
    """Run the full test suite with a specific configuration."""
    
    logger.info("")
    logger.info("┌" + "─" * 68 + "┐")
    logger.info(f"│ TEST SUITE: {config_name:<55} │")
    logger.info(f"│ Settings: {str(settings_update):<57} │")
    logger.info("└" + "─" * 68 + "┘")
    
    # Create specific output dir
    output_dir = OUTPUT_ROOT / config_name
    output_dir.mkdir(exist_ok=True, parents=True)
    logger.info(f"OUTPUT | Directory: {output_dir}")
    
    results = []
    
    with settings_context(settings_update, logger):
        # Allow settings to propagate (file watch delay etc)
        time.sleep(1.0)
        
        for gui_id, script_path, title_configs, file_type, extra_args in GUI_LIST:
            # Apply filter
            if gui_filter and gui_filter.lower() not in gui_id.lower():
                continue
            
            # Check if already completed (resume mode)
            if resume and checkpoint_mgr and checkpoint_mgr.is_completed(gui_id):
                logger.info(f"")
                logger.info(f"SKIP | {gui_id} (already completed in previous session)")
                result = TestResult(gui_id)
                result.script_exists = True  # Assume it was tested before
                results.append(result)
                checkpoint_mgr.mark_skipped(gui_id)
                continue
            
            result = run_gui_test(
                gui_id, script_path, title_configs, file_type, extra_args, 
                test_files, output_dir, logger, resource_monitor,
                is_korean=(settings_update.get("LANGUAGE") == "ko" or 
                           (not settings_update.get("LANGUAGE") and _read_current_language() == "ko")),
                dev_mode=dev_mode
            )
            results.append(result)
            
            # Update checkpoint
            if checkpoint_mgr:
                if result.status == "PASS":
                    checkpoint_mgr.mark_completed(gui_id)
                elif result.status in ("IMPORT_FAIL", "WINDOW_FAIL"):
                    checkpoint_mgr.mark_failed(gui_id)
            
            # Small delay between tests
            time.sleep(0.5)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GUI Screenshot Automation (Enhanced)")
    parser.add_argument("filter", nargs="?", help="Filter by GUI id")
    parser.add_argument("--list", action="store_true", help="List available GUIs")
    parser.add_argument("--themes", action="store_true", help="Run Dark/En and Light/Ko cycles")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--reset-checkpoint", action="store_true", help="Reset checkpoint and start fresh")
    parser.add_argument("--verbose", action="store_true", help="Verbose console output")
    parser.add_argument("--dev", action="store_true", help="Developer mode: extra debug output for input/launch failures")
    args = parser.parse_args()
    
    # Check dependencies
    if not HAS_PIL:
        print("[WARN] PIL not installed: pip install Pillow")
    if not HAS_PYGETWINDOW:
        print("[WARN] pygetwindow not installed: pip install pygetwindow")
        print("[ERROR] pygetwindow required for screenshot capture")
        return 1
    if not HAS_PSUTIL:
        print("[WARN] psutil not installed: pip install psutil")
        print("[INFO] Resource monitoring will be limited")
    
    if args.list:
        print("Available GUIs:")
        for gui_id, script, (en, ko), ftype, _ in GUI_LIST:
            exists = "✓" if (SRC_DIR / script).exists() else "✗"
            print(f"  {exists} {gui_id:20} -> EN:{en} / KO:{ko}")
        return 0
    
    # Setup session
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger, log_path = setup_logging(session_id, args.verbose)
    
    # Setup checkpoint manager
    checkpoint_file = REPORT_DIR / "checkpoint.json"
    checkpoint_mgr = CheckpointManager(checkpoint_file)
    
    if args.reset_checkpoint:
        logger.info("CHECKPOINT | Resetting checkpoint data")
        checkpoint_mgr.reset()
    
    if args.resume:
        logger.info(f"CHECKPOINT | Resume mode enabled")
        logger.info(f"CHECKPOINT | Last session: {checkpoint_mgr.data.get('started_at', 'N/A')}")
        logger.info(f"CHECKPOINT | Completed: {len(checkpoint_mgr.data.get('completed', []))}")
        logger.info(f"CHECKPOINT | Failed: {len(checkpoint_mgr.data.get('failed', []))}")
    else:
        checkpoint_mgr.start_session(session_id)
    
    # Setup resource monitor
    resource_monitor = ResourceMonitor(logger)
    resource_monitor.log_system_stats("INITIAL")
    
    logger.info(f"DEPENDENCIES | PIL: {HAS_PIL} | pygetwindow: {HAS_PYGETWINDOW} | psutil: {HAS_PSUTIL}")
    
    test_files = create_test_files(logger)
    all_results = []
    
    try:
        if args.themes:
            # Run Dark/English
            results_dark = run_test_suite(
                "dark_en", {"THEME": "Dark", "LANGUAGE": "en"}, 
                test_files, args.filter, logger, checkpoint_mgr, resource_monitor, args.resume, args.dev
            )
            all_results.extend(results_dark)
            
            # Run Light/Korean
            results_light = run_test_suite(
                "light_ko", {"THEME": "Light", "LANGUAGE": "ko"}, 
                test_files, args.filter, logger, checkpoint_mgr, resource_monitor, args.resume, args.dev
            )
            all_results.extend(results_light)
        else:
            # Default run (current settings)
            results = run_test_suite(
                "default", {}, test_files, args.filter, 
                logger, checkpoint_mgr, resource_monitor, args.resume, args.dev
            )
            all_results.extend(results)
        
    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 70)
        logger.warning("TEST INTERRUPTED BY USER")
        logger.warning("=" * 70)
        logger.warning("You can resume with: python capture_gui_screenshots.py --resume")
        return 130
    
    except Exception as e:
        logger.critical("")
        logger.critical("=" * 70)
        logger.critical(f"CRITICAL ERROR: {e}")
        logger.critical("=" * 70)
        logger.critical(traceback.format_exc())
        return 1
    
    finally:
        # Cleanup temp files
        try:
            shutil.rmtree(TEMP_DIR)
            logger.info(f"CLEANUP | Removed temp files: {TEMP_DIR}")
        except Exception as e:
            logger.warning(f"CLEANUP | Failed to remove temp files: {e}")
        
        # Final resource check
        resource_monitor.log_system_stats("FINAL")
    
    # Print summary
    print_summary(all_results, logger)
    
    # Save JSON report
    report_path = REPORT_DIR / f"report_{session_id}.json"
    save_json_report(all_results, report_path, logger)
    
    logger.info("")
    logger.info(f"LOG FILE: {log_path}")
    logger.info(f"REPORT FILE: {report_path}")
    logger.info(f"GUI LOGS: {REPORT_DIR / 'gui_logs'}")
    
    # Return exit code
    failures = sum(1 for r in all_results if r.status in ("IMPORT_FAIL", "WINDOW_FAIL"))
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
