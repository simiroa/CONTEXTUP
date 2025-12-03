import sys
import os
import traceback
from pathlib import Path
from tkinter import messagebox

# Add src to path so we can import modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.logger import setup_logger

# Setup logging
logger = setup_logger("menu_dispatcher")

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
            
            # This will block for a short time (0.2s) to collect other processes
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
        
        # 1. Custom Command Dispatch
        if item_config and item_config.get('command'):
            cmd_template = item_config['command']
            logger.info(f"Executing custom command: {cmd_template}")
            
            # Replace placeholders
            # %1 -> target_path
            # %V -> target_path (verbose/standard)
            cmd = cmd_template.replace("%1", str(target_path)).replace("%V", str(target_path))
            
            # Execute
            import subprocess
            subprocess.Popen(cmd, shell=True)
            return

        # 2. Legacy Hardcoded Dispatch
        logger.debug("Importing scripts...")
        from scripts import image_tools, sys_tools, video_tools, audio_tools, mayo_tools, upscale_tools
        
        logger.debug(f"Dispatching {item_id}...")
        if item_id.startswith("image_") or item_id.startswith("tex_"):
            if item_id == "image_format_convert":
                image_tools.convert_format(target_path)
            elif item_id == "image_remove_exif":
                image_tools.remove_exif(target_path)
            elif item_id == "image_resize_pot":
                image_tools.resize_pot(target_path)
            elif item_id == "image_exr_split":
                image_tools.exr_split(target_path)
            elif item_id == "image_exr_merge":
                image_tools.exr_merge(target_path)
            elif item_id == "image_upscale_ai":
                upscale_tools.upscale_image(target_path)
            elif item_id == "image_remove_bg_ai":
                from scripts import ai_tools
                ai_tools.remove_background(target_path)
            elif item_id == "image_analyze_ollama":
                from scripts import ollama_tools
                ollama_tools.analyze_image(target_path)

            else:
                logger.warning(f"Unknown image tool: {item_id}")

        elif item_id.startswith("ai_"):
            from scripts.ai_standalone import gemini_img_tools
            
            start_tab = "Style"
            if item_id == "ai_gemini_tools": start_tab = "Style"
            elif item_id == "ai_style_change": start_tab = "Style"
            elif item_id == "ai_pbr_gen": start_tab = "PBR Gen"
            elif item_id == "ai_maketile": start_tab = "Tileable"
            elif item_id == "ai_weathering": start_tab = "Weathering"
            elif item_id == "ai_to_prompt": start_tab = "Analysis"
            elif item_id == "ai_outpaint": start_tab = "Outpaint"
            elif item_id == "ai_inpaint": start_tab = "Inpaint"
            
            gemini_img_tools.GeminiImageToolsGUI(target_path, start_tab=start_tab).mainloop()

        elif item_id.startswith("sys_") or item_id.startswith("cad_") or item_id.startswith("doc_"):
            if item_id == "sys_manager_gui":
                manager_script = src_dir / "scripts" / "manager_gui.py"
                import subprocess
                subprocess.Popen([sys.executable, str(manager_script)])
            elif item_id == "sys_pdf_merge":
                sys_tools.pdf_merge(target_path, selection=batch_selection)
            elif item_id == "sys_pdf_split":
                sys_tools.pdf_split(target_path)
            elif item_id == "sys_move_to_new_folder":
                sys_tools.move_to_new_folder(target_path, selection=batch_selection)
            elif item_id == "sys_clean_empty_dir":
                sys_tools.clean_empty_dir(target_path)
            elif item_id == "sys_arrange_sequences":
                sys_tools.arrange_sequences(target_path, selection=batch_selection)
            elif item_id == "sys_find_missing_frames":
                sys_tools.find_missing_frames(target_path, selection=batch_selection)
            elif item_id == "sys_clipboard_ai":
                script_path = src_dir / "scripts" / "ai_standalone" / "clipboard_ai_tool.py"
                import subprocess
                subprocess.Popen([sys.executable, str(script_path)])
            elif item_id == "sys_save_clipboard":
                sys_tools.save_clipboard_image(target_path)
            elif item_id == "doc_analyze_ollama":
                from scripts import ollama_tools
                ollama_tools.analyze_document(target_path)
            elif item_id == "sys_open_recent":
                recent_script = src_dir / "scripts" / "sys_open_last.py"
                import subprocess
                subprocess.Popen([sys.executable, str(recent_script)])
            elif item_id == "sys_translator":
                trans_script = src_dir / "scripts" / "sys_translator.py"
                import subprocess
                subprocess.Popen([sys.executable, str(trans_script)])
            else:
                logger.warning(f"Unknown sys tool: {item_id}")
                
        elif item_id.startswith("video_"):
            if item_id == "video_seq_to_video":
                video_tools.seq_to_video(target_path)
            elif item_id == "video_convert":
                video_tools.convert_video(target_path)
            elif item_id == "video_frame_interp":
                from scripts.frame_interp_tools import interpolate_frames
                interpolate_frames(target_path)
            elif item_id == "video_frame_interp_30fps":
                video_tools.frame_interp_30fps(target_path)
            elif item_id == "video_generate_subtitle":
                from scripts import subtitle_tools
                subtitle_tools.generate_subtitles(target_path)
            elif item_id == "video_audio_tools":
                # Unified GUI for Extract/Remove/Separate
                script_path = src_dir / "scripts" / "audio_studio_gui.py"
                subprocess.Popen([sys.executable, str(script_path), str(target_path), "--tab", "video"])
            elif item_id == "video_downloader_gui":
                script_path = src_dir / "scripts" / "video_downloader_gui.py"
                import subprocess
                subprocess.Popen([sys.executable, str(script_path)])
            else:
                logger.warning(f"Unknown video tool: {item_id}")
                
        elif item_id.startswith("audio_"):
            script_path = src_dir / "scripts" / "audio_studio_gui.py"
            if item_id == "audio_convert_format":
                subprocess.Popen([sys.executable, str(script_path), str(target_path), "--tab", "convert"])
            elif item_id == "audio_separate":
                subprocess.Popen([sys.executable, str(script_path), str(target_path), "--tab", "separate"])
            elif item_id == "audio_optimize_vol":
                audio_tools.optimize_volume(target_path)
            else:
                logger.warning(f"Unknown audio tool: {item_id}")
        
        elif item_id.startswith("mesh_"):
            from scripts import blender_tools
            if item_id == "mesh_convert_format":
                blender_tools.convert_mesh(target_path)
            elif item_id == "mesh_auto_lod":
                script_path = src_dir / "scripts" / "mesh_lod_gui.py"
                import subprocess
                subprocess.Popen([sys.executable, str(script_path), str(target_path)])
            elif item_id == "mesh_extract_textures":
                blender_tools.extract_textures(target_path)
            else:
                logger.warning(f"Unknown mesh tool: {item_id}")

        elif item_id.startswith("mayo_"):
            if item_id == "mayo_open":
                mayo_tools.open_with_mayo(target_path)
            else:
                logger.warning(f"Unknown mayo tool: {item_id}")
        
        logger.debug("Dispatch complete.")

    except Exception as e:
        error_msg = f"Error executing {sys.argv}: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Context Menu Error", f"An error occurred:\n{e}")
        except:
            pass

if __name__ == "__main__":
    main()
