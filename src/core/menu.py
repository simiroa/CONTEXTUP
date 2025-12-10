import sys
import os
import traceback
from pathlib import Path
from tkinter import messagebox
import importlib
import subprocess

# Add src to path so we can import modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.logger import setup_logger

# Setup logging
logger = setup_logger("menu_dispatcher")


def _lazy(module_name, func_name):
    def _call(*args, **kwargs):
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        return func(*args, **kwargs)
    return _call


def _ai_tab_handler(item_id):
    from scripts.ai_standalone import gemini_img_tools
    tab_map = {
        "ai_style_change": "Style",
        "ai_pbr_gen": "PBR Gen",
        "ai_maketile": "Tileable",
        "ai_weathering": "Weathering",
        "ai_to_prompt": "Analysis",
        "ai_outpaint": "Outpaint",
        "ai_inpaint": "Inpaint",
    }
    return gemini_img_tools.GeminiImageToolsGUI, tab_map.get(item_id, "Style")


def _open_manager():
    """Robustly open the Manager GUI matching tray_agent logic."""
    try:
        manager_script = src_dir / "scripts" / "manager_gui.py"
        monitor_cmd = [sys.executable, str(manager_script)]
        
        # Log launch attempt
        log_path = Path("C:/Users/HG/manager_crash.log")
        
        # CREATE_NO_WINDOW = 0x08000000
        # We MUST keep the file handles open for the subclass? No, Popen handles it.
        # But we can't use 'with open' context manager easily here if we want Popen to keep running.
        # Actually we can, we just pass the file object.
        
        out_file = open(log_path, "w", encoding="utf-8")
        out_file.write(f"Launching: {monitor_cmd}\n")
        out_file.flush()
        
        # Launch with stdout/stderr redirection
        subprocess.Popen(
            monitor_cmd, 
            close_fds=True, 
            creationflags=0x08000000, 
            stdout=out_file, 
            stderr=out_file
        )
        
        # Note: We are leaking the file handle 'out_file' here in the parent process slightly, 
        # but since this process (menu.py) exits immediately (it's a transient dispatcher), it's fine.
        # The child inherits the handle? No, subprocess copies it.
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch Manager: {e}")


def build_handler_map():
    """
    Build the handler map (id -> callable or sentinel).
    Exposed for testing to ensure config/menu dispatch stays in sync.
    """
    return {
        # Image
        "image_format_convert": _lazy("scripts.gemini_image_tools", "convert_format"),
        "img_remove_exif": _lazy("scripts.gemini_image_tools", "remove_exif"),
        "img_resize_pot": _lazy("scripts.gemini_image_tools", "resize_pot"),
        "img_split_exr": _lazy("scripts.gemini_image_tools", "exr_split"),
        "img_merge_exr": _lazy("scripts.gemini_image_tools", "exr_merge"),
        "img_upscale_ai": _lazy("scripts.upscale_tools", "upscale_image"),
        "img_remove_bg": _lazy("scripts.ai_tools", "remove_background"),
        "img_marigold_pbr": _lazy("scripts.marigold_gui", "run_marigold_gui"),
        "ai_analyze_img": _lazy("scripts.prompt_master", "open_prompt_master"),
        "ai_img_lab": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "ai_standalone" / "gemini_img_tools.py"), str(p) if 'p' in locals() else ""]),

        # AI (Gemini image tools)
        "ai_style_change": "ai_tab",
        "ai_pbr_gen": "ai_tab",
        "ai_maketile": "ai_tab",
        "ai_weathering": "ai_tab",
        "ai_to_prompt": "ai_tab",
        "ai_outpaint": "ai_tab",
        "ai_inpaint": "ai_tab",
        # Sys / Doc / CAD
        "app_manager": lambda p, s=None: _open_manager(),
        "doc_pdf_merge": lambda p, s=None: _lazy("scripts.sys_tools", "pdf_merge")(p, selection=s),
        "doc_pdf_split": _lazy("scripts.sys_tools", "pdf_split"),
        "file_move_in_new_folder": lambda p, s=None: _lazy("scripts.sys_tools", "move_to_new_folder")(p, selection=s),
        "dir_clean_empty": _lazy("scripts.sys_tools", "clean_empty_dirs"),
        "vid_arrange_sequence": lambda p, s=None: _lazy("scripts.sys_tools", "arrange_sequences")(p, selection=s),
        "vid_find_missing_frames": lambda p, s=None: _lazy("scripts.sys_tools", "find_missing_frames")(p, selection=s),
        "clipboard_copy_info_legacy": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "ai_standalone" / "clipboard_ai_tool.py")]),
        "clipboard_save_image": _lazy("scripts.sys_tools", "save_clipboard_image"),
        "doc_analyze_ollama": _lazy("scripts.prompt_master", "open_prompt_master"),
        "clipboard_open_from_path": lambda p, s=None: _lazy("scripts.tray_modules.clipboard_opener", "open_folder_from_clipboard")(),
        "clipboard_copy_info": lambda p, s=None: _lazy("scripts.tray_modules.my_info", "show_my_info_menu")(),
        "file_reopen_recent": "recent_folder",
        "tool_translator": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "tool_translator.py")]),
        "rename_batch": _lazy("scripts.rename_tools", "run_rename_gui"),
        "rename_sequence": _lazy("scripts.rename_tools", "run_renumber_gui"),
        "tool_analyze_clipboard": _lazy("scripts.prompt_master", "open_prompt_master"),
        "tool_analyze_error": _lazy("scripts.clipboard_tools", "analyze_error"),
        "3d_convert_obj": _lazy("scripts.mayo_tools", "convert_cad"),
        # Video
        "vid_from_sequence": _lazy("scripts.video_tools", "seq_to_video"),
        "vid_convert": _lazy("scripts.video_tools", "convert_video"),
        "vid_frame_interp": _lazy("scripts.frame_interp_tools", "interpolate_frames"),
        "vid_frame_interp_30fps": _lazy("scripts.video_tools", "frame_interp_30fps"),
        "vid_subtitle_gen": _lazy("scripts.subtitle_tools", "generate_subtitles"),
        "video_audio_tools": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "video"]),
        "video_downloader_gui": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "video_downloader_gui.py")]),
        
        # Audio
        "aud_convert": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "convert"]),
        "aud_separate_stems": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "separate"]),
        "aud_normalize": _lazy("scripts.audio_tools", "optimize_volume"),
        "aud_extract_bgm": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "filter"]),
        "aud_extract_voice": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "filter"]),

        # Video / Audio Misc
        "vid_create_proxy": _lazy("scripts.video_tools", "create_proxy"),
        "vid_extract_audio": _lazy("scripts.video_tools", "extract_audio"),
        "vid_mute": _lazy("scripts.video_tools", "remove_audio"),

        # Mesh / Mayo
        "mesh_convert_format": _lazy("scripts.blender_tools", "convert_mesh"),
        "mesh_auto_lod": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "mesh_lod_gui.py"), str(p)]),
        "mesh_extract_textures": _lazy("scripts.blender_tools", "extract_textures"),
        "mayo_open": _lazy("scripts.mayo_tools", "open_with_mayo"),
        # Prompt Master
        "prompt_master": _lazy("scripts.prompt_master", "open_prompt_master"),
        
        # System (New)
        "file_create_symlink": _lazy("scripts.sys_tools", "create_symlink"),
        "tool_finder": _lazy("scripts.finder", "open_finder"),
        "dir_flatten": _lazy("scripts.sys_tools", "flatten_directory"),
        "dir_unwrap": _lazy("scripts.sys_tools", "flatten_directory"),
    }


def main():
    try:
        if len(sys.argv) < 3:
            logger.error(f"Insufficient arguments: {sys.argv}")
            return

        item_id = sys.argv[1]
        target_path = sys.argv[2]

        logger.info(f"Invoked: {item_id} on {target_path}")

        # Batch Execution Logic (Debouncing)
        try:
            logger.debug("Checking batch context...")
            from utils.batch_runner import collect_batch_context

            batch_selection = collect_batch_context(item_id, target_path)

            if batch_selection is None:
                logger.info(f"Skipping {target_path} (follower process)")
                sys.exit(0)

            logger.info(f"Leader process for {len(batch_selection)} items: {batch_selection}")

        except Exception as e:
            logger.warning(f"Batch check failed: {e}")
            batch_selection = [Path(target_path)]

        # Load config to find the script handler
        logger.debug("Loading config...")
        config = MenuConfig()
        item_config = config.get_item_by_id(item_id)

        # Custom command in config takes priority
        if item_config and item_config.get('command'):
            cmd_template = item_config['command']
            logger.info(f"Executing custom command: {cmd_template}")
            cmd = cmd_template.replace("%1", str(target_path)).replace("%V", str(target_path))
            subprocess.Popen(cmd, shell=True)
            return

        handlers = build_handler_map()
        handler = handlers.get(item_id)

        if handler == "ai_tab":
            gui_cls, tab = _ai_tab_handler(item_id)
            gui_cls(target_path, start_tab=tab).mainloop()
        elif handler == "recent_folder":
            import socket
            import json
            UDP_IP = "127.0.0.1"
            UDP_PORT = 54321 # Fallback
            
            # fast read of handshake file
            try:
                handshake_path = src_dir.parent / "logs" / "tray_info.json"
                if handshake_path.exists():
                    data = json.loads(handshake_path.read_text(encoding="utf-8"))
                    if data.get("port"):
                        UDP_PORT = int(data["port"])
            except: 
                pass

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"reopen_recent", (UDP_IP, UDP_PORT))
                sock.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to communicate with Tray Agent: {e}\nIs it running?")
        elif handler:
            # Some handlers expect batch_selection
            try:
                handler(target_path, batch_selection)
            except TypeError:
                handler(target_path)
        else:
            logger.warning(f"Unknown item_id: {item_id}")

        logger.debug("Dispatch complete.")

    except Exception as e:
        error_msg = f"Error executing {sys.argv}: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Context Menu Error", f"An error occurred:\n{e}")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except (PermissionError, OSError) as e:
        # Check for Access Denied (WinError 5)
        is_access_denied = isinstance(e, PermissionError) or (isinstance(e, OSError) and getattr(e, 'winerror', 0) == 5)
        
        if is_access_denied:
            import ctypes
            import tkinter as tk
            from tkinter import messagebox
            
            # Hide Main Window
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            if messagebox.askyesno("Access Denied", "This action requires Administrator privileges.\n\nDo you want to retry as Administrator?"):
                # Relaunch with RunAs
                try:
                    params = " ".join([f'"{arg}"' for arg in sys.argv])
                    # sys.executable is python.exe. We need to pass the script and args.
                    # But sys.argv[0] is the script path usually.
                    # Reconstruct command line somewhat reliably.
                    
                    script = sys.argv[0]
                    args = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                    
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {args}', None, 1)
                    if ret <= 32:
                        messagebox.showerror("Error", "Elevation failed or cancelled.")
                except Exception as ex:
                    messagebox.showerror("Error", f"Failed to elevate: {ex}")
            else:
                pass # User cancelled
        else:
            # Re-raise other errors to be caught optionally or logged
            # But since we are at top level, maybe we should just log and show error?
            # main() already has a catch-all for generic exceptions, so this block is likely
            # catching things that bubbled up or were re-raised.
            logger.error(f"Top-level error: {e}")
