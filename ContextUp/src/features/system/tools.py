import os
import shutil
from pathlib import Path
from tkinter import simpledialog, messagebox, filedialog
import tkinter as tk

from core.logger import setup_logger
from utils.files import get_safe_path, shell_move
from utils.i18n import t

logger = setup_logger("sys_tools")

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()
    return root

def _run_admin_batch(bat_content):
    """Run batch commands as admin and wait for completion."""
    import tempfile
    import ctypes
    import os
    import time
    
    fd, bat_path = tempfile.mkstemp(suffix=".bat", text=True)
    done_path = bat_path + ".done"
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write("@echo off\nchcp 65001 > nul\n")
            f.write(bat_content)
            # Create done marker
            f.write(f'\necho done > "{done_path}"')
            f.write("\nif %errorlevel% neq 0 ( pause ) else ( timeout /t 1 > nul )")
            
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 1)
        
        if ret <= 32: # Execution failed
            return False
            
        # Wait for done marker (Timeout 30s)
        start_time = time.time()
        while time.time() - start_time < 30:
            if os.path.exists(done_path):
                return True
            time.sleep(0.1)
            
        return False # Timeout
        
    except Exception as e:
        messagebox.showerror("Error", f"Admin execution failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            import threading
            def cleanup():
                time.sleep(2)
                try: os.remove(bat_path)
                except: pass
                try: os.remove(done_path)
                except: pass
            threading.Thread(target=cleanup, daemon=True).start()
        except: pass

def _is_admin():
    """Check if the current process is running with administrator privileges."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def move_to_new_folder(target_path: str, selection=None):
    """
    선택한 파일들을 새 폴더로 이동하고 자동으로 이름 변경 모드로 진입합니다.
    .lnk 및 .bat 파일도 정상적으로 이동합니다.
    """
    try:
        from utils.explorer import get_selection_from_explorer, select_and_rename
        import time

        # 1. 기본 디렉토리 결정
        base_dir = Path(os.path.abspath(target_path))
        if base_dir.is_file():
            base_dir = base_dir.parent
        
        # 2. 선택 항목 가져오기
        if not selection:
            selection = get_selection_from_explorer(target_path)
        
        # 3. 유효한 경로만 필터링 - abspath 사용 (.lnk 파일 자체를 유지)
        valid_selection = []
        if selection:
            for p in selection:
                abs_path = os.path.abspath(str(p))
                if os.path.exists(abs_path):
                    valid_selection.append(Path(abs_path))
        
        # 4. 선택된 파일이 base_dir에 있는지 확인
        base_dir_str = str(base_dir).lower()
        movable_files = []
        for p in valid_selection:
            try:
                parent_str = str(p.parent).lower()
                if parent_str == base_dir_str:
                    movable_files.append(p)
            except Exception:
                continue
        
        # 5. 탐색기에서 선택을 가져오지 못했거나 매칭 실패시, 폴더 내 모든 항목 사용
        if not movable_files and base_dir.is_dir():
            logger.info(f"No valid selection, using all items in: {base_dir}")
            for item in base_dir.iterdir():
                abs_path = os.path.abspath(str(item))
                if os.path.exists(abs_path):
                    movable_files.append(Path(abs_path))
        
        if not movable_files:
            logger.warning("No movable files found")
            return

        # 6. 새 폴더 이름 결정
        if len(movable_files) == 1:
            candidate_name = movable_files[0].stem
        else:
            candidate_name = "New Folder"
        
        new_folder = base_dir / candidate_name
        if new_folder.exists():
            idx = 2
            while (base_dir / f"{candidate_name} ({idx})").exists():
                idx += 1
            new_folder = base_dir / f"{candidate_name} ({idx})"

        # 7. 폴더 생성
        try:
            new_folder.mkdir(parents=True, exist_ok=False)
        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            return

        # 8. 파일 이동 (shell_move 사용으로 UAC 대응)
        moved_count = 0
        for item in movable_files:
            dest = new_folder / item.name
            if dest.exists():
                dest = get_safe_path(dest)
            
            if shell_move(str(item), str(dest)):
                moved_count += 1

        # 9. 이름 변경 모드 진입 (잠시 대기 후 트리거)
        if moved_count > 0:
            time.sleep(0.3)
            select_and_rename(new_folder)

    except Exception as e:
        logger.error(f"Move to new folder failed: {e}")
        messagebox.showerror("오류", f"작업 실패: {e}")

def save_clipboard_image(target_path: str):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is None:
            messagebox.showinfo("Info", "No image in clipboard.")
            return
            
        dest_dir = Path(target_path)
        if dest_dir.is_file(): dest_dir = dest_dir.parent
        
        save_path = get_safe_path(dest_dir / "clipboard_01.png")
        img.save(save_path, "PNG")
        
    except Exception as e:
        messagebox.showerror("Error", f"Save failed: {e}")

def pdf_merge(target_path: str, selection=None):
    try:
        from pypdf import PdfWriter
        
        if not selection:
            from utils.explorer import get_selection_from_explorer
            selection = get_selection_from_explorer(target_path)
            if not selection:
                selection = [Path(target_path)]
            else:
                selection = [Path(p) for p in selection]
        
        selection = [Path(p) for p in selection]
            
        pdfs = [p for p in selection if p.suffix.lower() == '.pdf']
        
        if len(pdfs) < 2:
            # If folder selected, merge all inside?
            p = Path(target_path)
            if p.is_dir():
                pdfs = sorted([f for f in p.glob("*.pdf")])
            
        if len(pdfs) < 2:
            messagebox.showinfo("Info", "Select at least 2 PDF files.")
            return
            
        pdfs.sort()
        
        merger = PdfWriter()
        for pdf in pdfs:
            merger.append(str(pdf))
            
        dest = get_safe_path(pdfs[0].parent / "merged.pdf")
        merger.write(str(dest))
        merger.close()
        
        messagebox.showinfo("Success", f"Merged {len(pdfs)} PDFs to {dest.name}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Merge failed: {e}")

def pdf_split(target_path: str, selection=None):
    try:
        from pathlib import Path
        if not selection:
            from utils.explorer import get_selection_from_explorer
            selection = get_selection_from_explorer(target_path)
            if not selection:
                selection = [Path(target_path)]
            else:
                selection = [Path(p) for p in selection]
        else:
            selection = [Path(p) for p in selection]

        pdfs = [p for p in selection if p.suffix.lower() == '.pdf']
        if not pdfs:
            messagebox.showinfo("Info", "No PDF files selected.")
            return

        root = _get_root()
        
        # Ask for mode once for the whole batch
        mode = simpledialog.askstring("Split PDF", f"Mode for {len(pdfs)} files: 'pdf' (split) or 'png' (convert):", parent=root)
        if not mode: return
        mode = mode.lower()
        
        count = 0
        for path in pdfs:
            output_dir = get_safe_path(path.parent / path.stem)
            output_dir.mkdir(exist_ok=True)
            
            if 'pdf' in mode:
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(str(path))
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    out_path = get_safe_path(output_dir / f"{path.stem}_page_{i+1:03d}.pdf")
                    with open(out_path, "wb") as f:
                        writer.write(f)
                count += 1
            elif 'png' in mode or 'image' in mode:
                from pdf2image import convert_from_path
                try:
                    images = convert_from_path(str(path))
                    for i, image in enumerate(images):
                        out_path = get_safe_path(output_dir / f"{path.stem}_page_{i+1:03d}.png")
                        image.save(str(out_path), "PNG")
                    count += 1
                except Exception as e:
                    logging.error(f"PNG conversion failed for {path.name}: {e}")
            else:
                messagebox.showwarning("Warning", f"Unknown mode '{mode}' for {path.name}")

        messagebox.showinfo("Success", f"Split {count} PDF files.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Split failed: {e}")


def get_clipboard_files():
    """Get list of files from clipboard (CF_HDROP)."""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                return [Path(p) for p in data]
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass
    return []

def clipboard_to_new_folder(target_path: str):
    try:
        # Target path is the background folder
        dest_root = Path(target_path)
        if dest_root.is_file(): dest_root = dest_root.parent
        
        if not dest_root.is_dir(): return

        files = get_clipboard_files()
        if not files:
            messagebox.showinfo("Info", "Clipboard is empty or does not contain files.")
            return

        # Check if files exist
        files = [f for f in files if f.exists()]
        if not files: return

        # Ask for Name
        root = _get_root()
        new_name = simpledialog.askstring("Paste to New Folder", f"Create folder for {len(files)} items:", initialvalue="New Folder", parent=root)
        if not new_name: return
        
        new_name = "".join(c for c in new_name if c not in '<>:"/\\|?*')
        if not new_name.strip(): return

        new_folder = get_safe_path(dest_root / new_name)
        new_folder.mkdir(parents=True, exist_ok=False)

        # Copy Files
        count = 0
        errors = []
        for item in files:
            try:
                dest = new_folder / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest))
                else:
                    shutil.copy2(str(item), str(dest))
                count += 1
            except Exception as e:
                errors.append(f"{item.name}: {e}")

        if errors:
            msg = f"Copied {count} items.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5: msg += "\n..."
            messagebox.showwarning("Result", msg)

    except Exception as e:
        messagebox.showerror("Error", f"Operation failed: {e}")

def copy_unc_path(target_path: str):
    try:
        import pyperclip
        
        # Check if we have a selection via Explorer
        from utils.explorer import get_selection_from_explorer
        selection = get_selection_from_explorer(target_path)
        
        if selection:
            # Use abspath instead of resolve to preserve .lnk file paths
            p = Path(os.path.abspath(str(selection[0])))
        else:
            p = Path(os.path.abspath(target_path))
            
        # Convert to UNC if mapped drive
        try:
            import win32wnet
            drive = p.drive
            if drive:
                remote = win32wnet.WNetGetConnection(drive)
                unc_path = str(p).replace(drive, remote, 1)
                pyperclip.copy(unc_path)
                return
        except:
            pass
            
        pyperclip.copy(str(p))
    except Exception as e:
        messagebox.showerror("Error", f"Copy failed: {e}")


def _get_target_files(target_path: str, allow_folder_content=False):
    """Get target files with proper validation and fallback."""
    from utils.explorer import get_selection_from_explorer
    
    base_dir = Path(os.path.abspath(target_path))
    if base_dir.is_file():
        base_dir = base_dir.parent
    base_dir_str = str(base_dir).lower()
    
    # Try to get selection from explorer
    selection = get_selection_from_explorer(target_path)
    
    # Validate selection - must be in base_dir
    valid_files = []
    if selection:
        for p in selection:
            abs_path = os.path.abspath(str(p))
            if os.path.exists(abs_path):
                p_path = Path(abs_path)
                if str(p_path.parent).lower() == base_dir_str:
                    valid_files.append(p_path)
    
    if valid_files:
        return valid_files
    
    # Fallback: single file
    p = Path(os.path.abspath(target_path))
    if p.is_file():
        return [p]
    
    # Fallback: folder contents
    if allow_folder_content and base_dir.is_dir():
        return [Path(os.path.abspath(str(f))) for f in base_dir.iterdir() if f.is_file()]
        
    return []


def clean_empty_dirs(target_path: str):
    path = Path(target_path)
    if not path.is_dir():
        messagebox.showwarning("Warning", "Please select a folder.")
        return
 
    if not messagebox.askyesno("Confirm", f"Remove all empty subdirectories in {path.name}?"):
        return
 
    removed_count = 0
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                d = Path(root) / name
                try:
                    if not any(d.iterdir()):
                        d.rmdir()
                        removed_count += 1
                except OSError:
                    pass
        
        messagebox.showinfo("Success", f"Removed {removed_count} empty directories.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clean: {e}")

# Backward compatibility: legacy name used in dispatcher
def clean_empty_dir(target_path: str):
    return clean_empty_dirs(target_path)
 


def _check_developer_mode():
    """Check if Windows Developer Mode is enabled (allows symlinks without admin)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
        )
        value, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevLicense")
        winreg.CloseKey(key)
        return value == 1
    except:
        return False

def create_symlink(target_path: str, selection=None):
    """
    Create a symbolic link to a folder.
    
    Note: On Windows, creating symlinks requires either:
    1. Administrator privileges, or
    2. Developer Mode enabled (Windows 10 version 1703+)
    """
    try:
        # 1. Determine where to put the link (Current Directory)
        # If the user clicked on a file background (target_path is folder), use it.
        # If user clicked on a file, use its parent.
        dest_dir = Path(target_path)
        if dest_dir.is_file():
            dest_dir = dest_dir.parent
            
        # 2. Ask user WHAT to link to
        root = _get_root()
        src_target_str = filedialog.askdirectory(parent=root, title="Select Folder to Link", initialdir=str(dest_dir))
        
        if not src_target_str: return # User cancelled
        
        src_target = Path(src_target_str)
        
        # 3. Determine Link Name
        link_name = f"{src_target.name} - Link"
        link_path = dest_dir / link_name
        
        # Collision check
        if link_path.exists():
            idx = 2
            while True:
                link_name = f"{src_target.name} - Link ({idx})"
                link_path = dest_dir / link_name
                if not link_path.exists(): break
                idx += 1

        # 4. Create Link (Try Normal -> Fallback to Admin)
        failed_due_to_privilege = False
        
        try:
            # os.symlink(target, link) -> creates a link at 'link' pointing to 'target'
            os.symlink(src_target, link_path)
            
            # Trigger Rename so user can type name immediately
            from utils.explorer import select_and_rename
            select_and_rename(link_path)
            
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 1314:
                failed_due_to_privilege = True
            else:
                messagebox.showerror("Error", f"Failed: {e}")
                return

        # 5. Admin Elevation Fallback with clear user guidance
        if failed_due_to_privilege:
            import ctypes
            
            # Check if developer mode is enabled
            dev_mode = _check_developer_mode()
            is_admin = _is_admin()
            
            # Show informative dialog first
            msg = "심볼릭 링크 생성에는 관리자 권한이 필요합니다.\n\n"
            
            if not dev_mode:
                msg += "💡 권장: Windows 개발자 모드를 활성화하면\n"
                msg += "   관리자 권한 없이도 심볼릭 링크를 생성할 수 있습니다.\n\n"
                msg += "   설정 → 업데이트 및 보안 → 개발자용 → 개발자 모드\n\n"
            
            msg += "관리자 권한으로 심볼릭 링크를 생성하시겠습니까?"
            
            if not messagebox.askyesno("관리자 권한 필요", msg):
                return
            
            import tempfile
            
            bat_lines = ["@echo off", "chcp 65001 > nul"]
            
            # mklink /D "Link" "Target"
            # Since we selected a folder via askdirectory, it is a directory link.
            cmd = f'mklink /D "{link_path}" "{src_target}"'
            bat_lines.append(cmd)
            
            bat_lines.append("if %errorlevel% neq 0 (")
            bat_lines.append("    echo.")
            bat_lines.append("    echo [ERROR] Failed to create symlink.")
            bat_lines.append("    pause")
            bat_lines.append(") else (")
            bat_lines.append("    echo.")
            bat_lines.append("    echo [SUCCESS] Symlink created successfully!")
            bat_lines.append("    timeout /t 2 > nul")
            bat_lines.append(")")
            
            fd, bat_path = tempfile.mkstemp(suffix=".bat", text=True)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write("\n".join(bat_lines))
                
                ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 1)
                
                if ret <= 32:
                    error_msg = "관리자 권한 요청이 거부되었거나 실패했습니다.\n\n"
                    error_msg += "해결 방법:\n"
                    error_msg += "1. 관리자 권한으로 ContextUp 실행\n"
                    error_msg += "2. Windows 개발자 모드 활성화\n"
                    error_msg += "   (설정 → 업데이트 및 보안 → 개발자용)"
                    messagebox.showerror("권한 오류", error_msg)
            except Exception as e:
                messagebox.showerror("Error", f"Elevation failed: {e}")
            finally:
                # Clean up temp file after a delay
                try:
                    import threading
                    def cleanup():
                        import time
                        time.sleep(5)
                        try:
                            os.remove(bat_path)
                        except:
                            pass
                    threading.Thread(target=cleanup, daemon=True).start()
                except:
                    pass

    except Exception as e:
        messagebox.showerror("Error", f"Failed to create symlink: {e}")

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
    try:
        # Allow folder content if background clicked
        if selection:
            files = [Path(p) for p in selection]
        else:
            files = _get_target_files(target_path, allow_folder_content=True)
            
        if not files: return
        
        # Identify Sequences
        import re
        sequences = {}
        pattern = re.compile(r"^(.*?)(\d+)(\.[a-zA-Z0-9]+)$")
        
        for f in files:
            # Skip hidden files
            if f.name.startswith('.'): continue
            
            match = pattern.match(f.name)
            if match:
                prefix, num_str, ext = match.groups()
                key = (prefix, ext, f.parent) # Group by parent too
                if key not in sequences:
                    sequences[key] = []
                sequences[key].append(int(num_str))
                
        if not sequences:
            messagebox.showinfo("Result", "No sequences found in selection.")
            return
            
        report_entries = []
        has_missing = False
        
        for (prefix, ext, parent), nums in sequences.items():
            nums.sort()
            missing = []
            if len(nums) > 1:
                # Optimized: iterate through sorted list to find gaps
                # Avoids memory explosion from set(range(min, max+1)) 
                for i in range(1, len(nums)):
                    gap_start = nums[i-1] + 1
                    gap_end = nums[i]
                    # Add all missing numbers in this gap
                    for m in range(gap_start, gap_end):
                        missing.append(m)
                
            if missing:
                has_missing = True
                missing_str = format_missing_ranges(missing)
                entry = (
                    f"Sequence: {prefix}*{ext}\n"
                    f"Location: {parent}\n"
                    f"Range: {nums[0]} - {nums[-1]} (Total: {len(nums)})\n"
                    f"Missing Count: {len(missing)}\n"
                    f"Missing Frames:\n{missing_str}\n"
                    f"{'-'*50}"
                )
                report_entries.append(entry)
            else:
                pass
                
        if not has_missing:
            messagebox.showinfo("Result", "No missing frames found in detected sequences.")
            return
            
        # Write to file
        from datetime import datetime
        import subprocess
        
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"MissingFrames_{date_str}.txt"
        
        # Save in the directory of the first file checked (or target_path)
        # Use target_path if valid directory, else parent of first file
        save_dir = Path(target_path)
        if not save_dir.is_dir():
            save_dir = files[0].parent
            
        out_path = get_safe_path(save_dir / filename)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Missing Frames Report - {date_str}\n")
            f.write(f"Scanned {len(files)} files in: {save_dir}\n")
            f.write("="*50 + "\n\n")
            f.write("\n\n".join(report_entries))
            
        # Open the file or show location
        try:
            os.startfile(out_path) # Windows only, but effective
        except:
             # Fallback
            subprocess.Popen(['notepad', str(out_path)])
            
        messagebox.showinfo("Export Complete", f"Missing frames report saved to:\n{out_path}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
 
def arrange_sequences(target_path: str, selection=None):
    try:
        if selection:
            files = [Path(p) for p in selection]
        else:
            files = _get_target_files(target_path, allow_folder_content=True)
            
        if not files: return
        
        import re
        pattern = re.compile(r"^(.*?)(\d+)(\.[a-zA-Z0-9]+)$")
        
        moves = {} 
        
        for f in files:
            match = pattern.match(f.name)
            if match:
                prefix, _, _ = match.groups()
                if not prefix: continue
                # Use parent of file as base
                dest = f.parent / prefix.strip(" _-.")
                if dest not in moves:
                    moves[dest] = []
                moves[dest].append(f)
                
        if not moves:
            messagebox.showinfo("Result", "No sequences detected.")
            return
            
        count = 0
        for dest, flist in moves.items():
            if len(flist) < 2: continue 
            
            dest.mkdir(exist_ok=True)
            for f in flist:
                if shell_move(str(f), str(dest / f.name)):
                    count += 1
                
        messagebox.showinfo("Success", f"Moved {count} files into {len(moves)} folders.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

def flatten_directory(target_path: str, selection=None):
    try:
        path = Path(target_path)
        if not path.is_dir():
            messagebox.showwarning(t("common.warning", "경고"), t("system.unwrap.select_folder", "폴더를 선택해주세요."))
            return

        # Unwrap logic: Move content to parent
        target_dest = path.parent
        
        # 1. Confirm Basic Unwrap
        msg_template = t("system.unwrap.confirm_msg", 
                         "'{name}' 폴더를 해제하여 '{dest}'(으)로 이동하시겠습니까?\n\n"
                         "파일들이 상위 폴더로 이동됩니다.\n"
                         "작업 후 빈 원래 폴더는 삭제됩니다.")
        
        msg = msg_template.format(name=path.name, dest=target_dest.name)
              
        if not messagebox.askyesno(t("system.unwrap.confirm_title", "폴더 풀기 확인"), msg):
            return

        # 2. Ask for Recursive
        recursive_msg = t("system.unwrap.recursive_msg",
                          "하위 폴더에 있는 파일들도 모두 꺼내시겠습니까?\n\n"
                          "[예] 모든 하위 파일들을 꺼내고 폴더 구조를 평탄화 (파일명 중복 시 자동 변경)\n"
                          "[아니오] 현재 폴더에 있는 것만 꺼내기 (하위 폴더는 폴더째로 이동)")
                          
        is_recursive = messagebox.askyesno(t("system.unwrap.recursive_title", "하위 폴더 포함"), recursive_msg)
        
        items_to_move = []
        
        if is_recursive:
             # Recursive: Get all files only
             for root, dirs, files in os.walk(path):
                 for name in files:
                     items_to_move.append(Path(root) / name)
        else:
             # Single Level: Immediate children (files and dirs)
             items_to_move = list(path.iterdir())
        
        if not items_to_move:
             messagebox.showinfo(t("common.info", "알림"), t("system.unwrap.folder_empty", "폴더가 비어있습니다."))
             try: path.rmdir()
             except: pass
             return

        moved_count = 0
        collision_count = 0
        errors = []
        
        for item in items_to_move:
            try:
                dest = target_dest / item.name
                
                # Auto-Rename logic for collisions
                if dest.exists():
                    dest = get_safe_path(dest)
                    collision_count += 1
                    
                if shell_move(str(item), str(dest)):
                    moved_count += 1
                else:
                    errors.append(f"{item.name}: 이동 실패 (사용자 취소 또는 권한 부족)")
            except Exception as e:
                errors.append(f"{item.name}: {e}")
                logger.error(f"Failed to move {item}: {e}")

        # Clean up empty folders if recursive (or original folder)
        if path.exists():
            try:
                if is_recursive:
                    # Remove empty subdirs bottom-up
                    for root, dirs, files in os.walk(path, topdown=False):
                        for name in dirs:
                            try: (Path(root) / name).rmdir()
                            except: pass
                
                path.rmdir() # Try to remove the target root itself
            except OSError:
                # Often fails due to desktop.ini or Thumbs.db
                # Force delete if only junk remains
                try:
                    # Re-check content
                    remaining = []
                    for root, dirs, files in os.walk(path):
                        for f in files: remaining.append(f)
                        
                    junk = {'.DS_Store', 'desktop.ini', 'Thumbs.db'}
                    is_junk_only = all(f.name in junk for f in remaining)
                    
                    if is_junk_only:
                        # Use global shutil
                        shutil.rmtree(path, ignore_errors=True)
                except:
                    pass 

        msg = t("system.unwrap.success_message", "총 {count}개 항목을 '{target}'(으)로 이동했습니다.", count=moved_count, target=target_dest.name)
        if collision_count > 0:
            msg += "\n" + t("system.unwrap.collision_info", "(이름 중복으로 {count}개 항목 이름 변경됨)", count=collision_count)
            
        if errors:
            msg += "\n\n" + t("system.unwrap.error_list", "오류 ({count}건):", count=len(errors)) + "\n" + "\n".join(errors[:5])
        
        messagebox.showinfo(t("common.complete", "완료"), msg)

    except Exception as e:
        messagebox.showerror(t("common.error", "오류"), t("system.unwrap.fail_message", "작업 실패: {error}", error=e))
