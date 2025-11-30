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
            elif item_id == "image_smart_tag":
                from scripts import metadata_tools
                metadata_tools.tag_images(target_path)
            elif item_id == "image_texture_tools":
                from scripts.ai_standalone import texture_gen
                texture_gen.TextureGenGUI().mainloop()
            else:
                logger.warning(f"Unknown image tool: {item_id}")

        elif item_id.startswith("sys_") or item_id.startswith("cad_") or item_id.startswith("doc_"):
            if item_id == "sys_pdf_merge":
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
            elif item_id == "sys_analyze_clipboard":
                from scripts import ollama_tools
                ollama_tools.analyze_clipboard_image(target_path)
            elif item_id == "sys_save_clipboard":
                sys_tools.save_clipboard_image(target_path)
            elif item_id == "sys_analyze_error":
                from scripts import ollama_tools
                ollama_tools.analyze_error(target_path)
            elif item_id == "sys_manager_gui":
                from scripts import manager_gui
                manager_gui.ManagerGUI().mainloop()
            elif item_id == "sys_batch_rename":
                from scripts import rename_tools
                rename_tools.run_rename_gui(target_path)
            elif item_id == "sys_renumber":
                from scripts import rename_tools
                rename_tools.run_renumber_gui(target_path)
            elif item_id == "cad_convert_obj":
                from scripts import mayo_tools
                mayo_tools.convert_to_obj(target_path)
            elif item_id == "doc_analyze_ollama":
                from scripts import ollama_tools
                ollama_tools.analyze_document(target_path)
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
                from scripts import video_audio_gui
                video_audio_gui.run_gui(target_path)
            else:
                logger.warning(f"Unknown video tool: {item_id}")
                
        elif item_id.startswith("audio_"):
            if item_id == "audio_convert_format":
                audio_tools.convert_format(target_path)
            elif item_id == "audio_optimize_vol":
                audio_tools.optimize_volume(target_path)
            else:
                logger.warning(f"Unknown audio tool: {item_id}")
        
        elif item_id.startswith("mesh_"):
            from scripts import blender_tools
            if item_id == "mesh_convert_format":
                blender_tools.convert_mesh(target_path)
            elif item_id == "mesh_extract_textures":
                blender_tools.extract_textures(target_path)
            else:
                logger.warning(f"Unknown mesh tool: {item_id}")
        
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
