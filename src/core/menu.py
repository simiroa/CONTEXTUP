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
        log_path = src_dir.parent / "logs" / "manager_crash.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
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
        # === Image ===
        "image_convert": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "image_convert_gui.py"), str(p)]),
        "merge_to_exr": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "exr_tools_gui.py"), str(p)]),
        "resize_power_of_2": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "image_resize_gui.py"), str(p)]),
        "split_exr": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "exr_tools_gui.py"), str(p)]),
        "texture_packer_orm": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "texture_packer_gui.py"), str(p)]),
        "normal_flip_green": _lazy("scripts.normal_tools", "flip_normal_green"),
        "simple_normal_roughness": _lazy("scripts.normal_tools", "generate_simple_normal_roughness"),

        # === AI ===
        "ocr_paddle": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "ai_standalone" / "pdf_ocr_tool.py"), str(p)]),
        "frame_interpolation_ai": _lazy("scripts.frame_interp_tools", "interpolate_frames"),
        "subtitle_ai": _lazy("scripts.subtitle_tools", "generate_subtitles"),
        "ai_upscale": _lazy("scripts.upscale_tools", "upscale_image"),
        "remove_background": _lazy("scripts.ai_tools", "remove_background"),
        "marigold_pbr": _lazy("scripts.marigold_gui", "run_marigold_gui"),
        "prompt_master": _lazy("scripts.prompt_master", "open_prompt_master"),
        "gemini_image_tool": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "ai_standalone" / "gemini_img_tools.py"), str(p)]),
        "separate_stems_ai": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "separate"]),

        # === Video ===
        "arrange_sequences": lambda p, s=None: _lazy("scripts.sys_tools", "arrange_sequences")(p, selection=s),
        "video_convert": _lazy("scripts.video_tools", "convert_video"),
        "extract_audio": _lazy("scripts.video_tools", "extract_audio"),
        "find_missing_frames": lambda p, s=None: _lazy("scripts.sys_tools", "find_missing_frames")(p, selection=s),
        "interpolate_30fps": _lazy("scripts.video_tools", "frame_interp_30fps"),
        "create_proxy": _lazy("scripts.video_tools", "create_proxy"),
        "remove_audio": _lazy("scripts.video_tools", "remove_audio"),
        "sequence_to_video": _lazy("scripts.video_tools", "seq_to_video"),

        # === Audio ===
        "audio_convert": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "convert"]),
        "extract_bgm": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "filter"]),
        "extract_voice": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "audio_studio_gui.py"), str(p), "--tab", "filter"]),
        "normalize_volume": _lazy("scripts.audio_tools", "optimize_volume"),

        # === System ===
        "clean_empty_folders": _lazy("scripts.sys_tools", "clean_empty_dirs"),
        "move_to_new_folder": lambda p, s=None: _lazy("scripts.sys_tools", "move_to_new_folder")(p, selection=s),
        "reopen_recent": "recent_folder",
        "unwrap_folder": _lazy("scripts.sys_tools", "flatten_directory"),
        "finder": _lazy("scripts.finder", "open_finder"),
        "create_symlink": _lazy("scripts.sys_tools", "create_symlink"),
        "manager": lambda p, s=None: _open_manager(),

        # === 3D ===
        "auto_lod": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "mesh_lod_gui.py"), str(p)]),
        "cad_to_obj": _lazy("scripts.mayo_tools", "convert_cad"),
        "mesh_convert": _lazy("scripts.blender_tools", "convert_mesh"),
        "open_with_mayo": _lazy("scripts.mayo_tools", "open_with_mayo"),
        "extract_textures": _lazy("scripts.blender_tools", "extract_textures"),

        # === Clipboard ===
        "copy_my_info": lambda p, s=None: _lazy("scripts.tray_modules.my_info", "show_my_info_menu")(),
        "analyze_error": _lazy("scripts.clipboard_tools", "analyze_error"),
        "open_from_clipboard": lambda p, s=None: _lazy("scripts.tray_modules.clipboard_opener", "open_folder_from_clipboard")(),
        "save_clipboard_image": _lazy("scripts.sys_tools", "save_clipboard_image"),
        "copy_unc_path": _lazy("scripts.sys_tools", "copy_unc_path"),

        # === Document ===
        "pdf_merge": lambda p, s=None: _lazy("scripts.sys_tools", "pdf_merge")(p, selection=s),
        "pdf_split": _lazy("scripts.sys_tools", "pdf_split"),

        # === Rename ===
        "batch_rename": _lazy("scripts.rename_tools", "run_rename_gui"),
        "renumber_sequence": _lazy("scripts.rename_tools", "run_renumber_gui"),

        # === Tools ===
        "youtube_downloader": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "video_downloader_gui.py")]),
        "translator": lambda p, s=None: subprocess.Popen([sys.executable, str(src_dir / "scripts" / "tool_translator.py")]),
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
