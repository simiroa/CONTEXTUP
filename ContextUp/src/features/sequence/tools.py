"""
Sequence Tools - Image Sequence Management
Functions for detecting, analyzing, and organizing image sequences.
"""
import os
import sys
import re
import shutil
from pathlib import Path
from tkinter import messagebox

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.logger import setup_logger
from utils.files import get_safe_path

logger = setup_logger("sequence_tools")


def _get_root():
    """Get Tkinter root for dialogs."""
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def shell_move(src, dst):
    """
    Move file or folder using Windows Shell API (supports undo, retry dialogs, etc).
    Returns True on success, False on failure.
    """
    try:
        import win32com.shell.shell as shell
        from win32com.shell import shellcon
        
        # Use FOF flags for friendly behavior
        result = shell.SHFileOperation((
            0,  # hwnd
            shellcon.FO_MOVE,
            src,
            dst,
            shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_ALLOWUNDO,
            None,
            None
        ))
        
        return result[0] == 0
        
    except Exception as e:
        logger.warning(f"Shell move failed, falling back to shutil: {e}")
        try:
            shutil.move(src, dst)
            return True
        except:
            return False


def get_folder_sequences(folder_path: Path) -> dict:
    """
    Scan a folder and detect all image sequences.
    
    Returns dict: {(prefix, ext): [(frame_num, file_path), ...]}
    """
    # Pattern to match: prefix + number sequence (3+ digits) + extension
    # Using greedy .+ to capture everything before the LAST number sequence
    # Example: "sc03_test_0001.png" -> prefix="sc03_test_", num="0001", ext=".png"
    # Example: "render5_0123.exr" -> prefix="render5_", num="0123", ext=".exr"
    pattern = re.compile(r"^(.+?)(\d{3,})(\.[a-zA-Z0-9]+)$")
    sequences = {}
    
    if not folder_path.is_dir():
        return sequences
    
    for f in folder_path.iterdir():
        if f.is_file() and not f.name.startswith('.'):
            match = pattern.match(f.name)
            if match:
                prefix, num_str, ext = match.groups()
                key = (prefix, ext)
                if key not in sequences:
                    sequences[key] = []
                sequences[key].append((int(num_str), f))
    
    # Sort each sequence by frame number
    for key in sequences:
        sequences[key].sort(key=lambda x: x[0])
    
    return sequences


def format_missing_ranges(missing_frames: list) -> str:
    """Format a list of numbers into ranges (e.g. '101-105, 107, 109-112')."""
    if not missing_frames:
        return ""
        
    ranges = []
    start = missing_frames[0]
    prev = start
    
    for x in missing_frames[1:]:
        if x == prev + 1:
            prev = x
        else:
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            start = x
            prev = x
            
    # Last group
    if start == prev:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{prev}")
        
    return ", ".join(ranges)


def find_missing_frames(target_path: str, selection=None):
    """
    Find missing frames in image sequences within a folder.
    Folder-based operation: analyzes all sequences inside the selected folder.
    """
    try:
        folder = Path(target_path)
        if not folder.is_dir():
            messagebox.showwarning("Warning", "Please select a folder containing image sequences.")
            return
        
        sequences = get_folder_sequences(folder)
        
        if not sequences:
            messagebox.showinfo("Result", "No sequences found in folder.")
            return
            
        report_entries = []
        has_missing = False
        
        for (prefix, ext), frames in sequences.items():
            nums = [f[0] for f in frames]
            missing = []
            
            if len(nums) > 1:
                # Find gaps in sequence
                for i in range(1, len(nums)):
                    gap_start = nums[i-1] + 1
                    gap_end = nums[i]
                    for m in range(gap_start, gap_end):
                        missing.append(m)
                
            if missing:
                has_missing = True
                missing_str = format_missing_ranges(missing)
                entry = (
                    f"Sequence: {prefix}*{ext}\n"
                    f"Location: {folder}\n"
                    f"Range: {nums[0]} - {nums[-1]} (Total: {len(nums)})\n"
                    f"Missing Count: {len(missing)}\n"
                    f"Missing Frames:\n{missing_str}\n"
                    f"{'-'*50}"
                )
                report_entries.append(entry)
                
        if not has_missing:
            messagebox.showinfo("Result", "No missing frames found in detected sequences.")
            return
            
        # Write to file
        from datetime import datetime
        import subprocess
        
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"MissingFrames_{date_str}.txt"
        out_path = get_safe_path(folder / filename)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Missing Frames Report - {date_str}\n")
            f.write(f"Scanned folder: {folder}\n")
            f.write("="*50 + "\n\n")
            f.write("\n\n".join(report_entries))
            
        # Open the file
        try:
            os.startfile(out_path)
        except:
            subprocess.Popen(['notepad', str(out_path)])
            
        messagebox.showinfo("Export Complete", f"Missing frames report saved to:\n{out_path}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")


def shell_move_batch(src_files: list, dest_folder: str):
    """
    Move multiple files to a destination folder using Windows Shell API in one operation.
    Much faster than moving files one by one.
    
    Args:
        src_files: List of source file paths (strings)
        dest_folder: Destination folder path (string)
    
    Returns:
        (success_count, failed_files) tuple
    """
    try:
        import win32com.shell.shell as shell
        from win32com.shell import shellcon
        
        # Create NULL-separated string for source files
        src_string = '\0'.join(str(f) for f in src_files) + '\0'
        
        # Use FOF flags for silent, fast operation
        # NOTE: Do NOT use FOF_MULTIDESTFILES - we have ONE destination for all files
        result = shell.SHFileOperation((
            0,  # hwnd
            shellcon.FO_MOVE,
            src_string,
            dest_folder + '\0',  # NULL-terminated destination
            shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_ALLOWUNDO,
            None,
            None
        ))
        
        # result[0] == 0 means success
        if result[0] == 0:
            return len(src_files), []
        else:
            # If batch fails, fall back to individual moves to identify problems
            success = 0
            failed = []
            for f in src_files:
                if shell_move(str(f), str(Path(dest_folder) / Path(f).name)):
                    success += 1
                else:
                    failed.append(Path(f).name)
            return success, failed
            
    except Exception as e:
        logger.warning(f"Batch shell move failed, falling back to individual: {e}")
        # Fallback to individual moves
        success = 0
        failed = []
        for f in src_files:
            try:
                dest_path = Path(dest_folder) / Path(f).name
                shutil.move(str(f), str(dest_path))
                success += 1
            except Exception:
                failed.append(Path(f).name)
        return success, failed


def arrange_sequences(target_path: str, selection=None):
    """
    Organize files in a folder into sequence-based subfolders.
    Folder-based operation: groups sequences inside the selected folder.
    """
    try:
        folder = Path(target_path)
        if not folder.is_dir():
            messagebox.showwarning("Warning", "Please select a folder containing image sequences.")
            return
        
        sequences = get_folder_sequences(folder)
        
        if not sequences:
            messagebox.showinfo("Result", "No sequences detected in folder.")
            return
        
        # Filter sequences by minimum file count
        min_files = 2
        filtered_sequences = {k: v for k, v in sequences.items() if len(v) >= min_files}
        
        if not filtered_sequences:
            single_count = sum(len(v) for v in sequences.values())
            messagebox.showinfo("Result", f"Found only {single_count} single files (no sequences with {min_files}+ frames).")
            return
        
        # Prepare folder mapping
        folder_mapping = {}  # dest_folder -> list of file paths
        
        for (prefix, ext), frames in filtered_sequences.items():
            # Create subfolder based on prefix
            # Strip trailing non-alphanumeric characters (like _, -, ., space, etc.)
            folder_name = prefix.rstrip(" _-.~!@#$%^&*()+=[]{}|\\:;\"'<>,?/")
            
            # If nothing left, use extension as fallback
            if not folder_name or not folder_name.strip():
                folder_name = f"sequence_{ext[1:]}"  # Remove the dot from extension
            
            dest_folder = folder / folder_name
            
            if dest_folder not in folder_mapping:
                folder_mapping[dest_folder] = []
            
            # Add all file paths for this sequence
            folder_mapping[dest_folder].extend([f for _, f in frames])
        
        # Create all folders at once
        created_folders = set()
        for dest_folder in folder_mapping.keys():
            try:
                dest_folder.mkdir(exist_ok=True)
                created_folders.add(dest_folder)
            except Exception as e:
                logger.error(f"Failed to create folder {dest_folder}: {e}")
        
        # Move files in batch per destination folder
        total_moved = 0
        all_errors = []
        
        for dest_folder, file_list in folder_mapping.items():
            if dest_folder not in created_folders:
                continue  # Skip if folder creation failed
            
            # Move all files to this destination in one batch operation
            success_count, failed_files = shell_move_batch(
                [str(f) for f in file_list],
                str(dest_folder)
            )
            
            total_moved += success_count
            all_errors.extend(failed_files)
        
        # Report results
        msg = f"Moved {total_moved} files into {len(created_folders)} folders."
        if all_errors:
            msg += f"\n\nFailed to move {len(all_errors)} files."
            if len(all_errors) <= 5:
                msg += f"\n{', '.join(all_errors)}"
            else:
                msg += f"\n{', '.join(all_errors[:5])}... and {len(all_errors) - 5} more."
        
        messagebox.showinfo("Success", msg)
        
    except Exception as e:
        logger.error(f"arrange_sequences failed: {e}")
        messagebox.showerror("Error", f"Failed: {e}")


def seq_to_video(target_path: str):
    """
    Launch Sequence to Video GUI for the selected folder.
    Folder-based operation: converts sequences in folder to video.
    """
    import subprocess
    
    folder = Path(target_path)
    if not folder.is_dir():
        messagebox.showwarning("Warning", "Please select a folder containing image sequences.")
        return
    
    # Launch the GUI
    gui_script = current_dir / "to_video_gui.py"
    if gui_script.exists():
        subprocess.Popen([sys.executable, str(gui_script), str(folder)])
    else:
        messagebox.showerror("Error", f"GUI script not found: {gui_script}")
