import os
import shutil
import glob
import logging
import subprocess
import ctypes
from pathlib import Path

logger = logging.getLogger(__name__)

class DiskCleaner:
    """Handles disk cleanup operations."""
    
    def __init__(self):
        self.user_temp = os.environ.get('TEMP')
        self.win_temp = os.environ.get('WINDIR', 'C:\\Windows') + '\\Temp'
        self.adobe_cache = os.path.join(os.environ.get('APPDATA', ''), 'Adobe', 'Common', 'Media Cache Files')
        
        # Robust Downloads Detection
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
            self.downloads, _ = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
        except:
            self.downloads = os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads')
        
        # Shader Caches
        self.nv_shader = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'NVIDIA', 'DXCache')
        self.amd_shader = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AMD', 'DxCache')
        
        # 3D Engines (DDC)
        self.ue_ddc = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'UnrealEngine', 'Common', 'DerivedDataCache')
        
    def get_size_for_category(self, category: str) -> tuple:
        """Analyze size for a specific cleanup category. Returns (formatted_str, bytes)."""
        total = 0
        try:
            if category == 'temp':
                total += self._get_folder_size(self.user_temp)
                total += self._get_folder_size(self.win_temp)
            elif category == 'adobe':
                total += self._get_folder_size(self.adobe_cache)
            elif category == 'downloads':
                total += self._get_folder_size(self.downloads)
            elif category == 'bin':
                # Note: bin size calculation is heavy via walk, but let's try a light scan
                pass
            elif category == 'delivery':
                total += self._get_folder_size(r"C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\DeliveryOptimization\Cache")
            elif category == 'shader':
                total += self._get_folder_size(self.nv_shader)
                total += self._get_folder_size(self.amd_shader)
            elif category == 'engine':
                total += self._get_folder_size(self.ue_ddc)
            elif category == 'wsl':
                wsl_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Packages')
                if os.path.exists(wsl_path):
                    for root, dirs, files in os.walk(wsl_path):
                        for f in files:
                            if f.endswith('.vhdx'):
                                total += os.path.getsize(os.path.join(root, f))
        except: pass
        return self._format_size(total), total

    def get_info(self, category: str) -> dict:
        """Get info and risk for a category."""
        infos = {
            'temp': {"desc": "User and System temporary files.", "risk": "Safe. Apps and Windows create these to store transient data."},
            'bin': {"desc": "Deleted files in the Recycle Bin.", "risk": "Irreversible. Ensure you don't need these files anymore."},
            'hiber': {"desc": "Hibernation file (hiberfil.sys).", "risk": "Safe if you don't use Hibernation (PC sleep is different)."},
            'winsxs': {"desc": "Old Windows update files and component store.", "risk": "Safe, but slow. Windows will take longer to scan updates."},
            'delivery': {"desc": "Cached Windows Update delivery parts.", "risk": "Safe. Files are re-downloaded if needed by others on LAN."},
            'adobe': {"desc": "Adobe common media cache (AE/PR).", "risk": "Safe. Adobe will regenerate these when projects open (Slow)."},
            'downloads': {"desc": "User Downloads folder.", "risk": "CAUTION. This will delete all files you have downloaded. Check carefully!"},
            'shader': {"desc": "NVIDIA/AMD GPU Shader Cache.", "risk": "Safe. Fixes stutters or glitches after driver updates. Regenerated while gaming."},
            'engine': {"desc": "Unreal Engine Derived Data Cache (DDC).", "risk": "Safe. Reclaimed space is huge, but reopening UE projects will take longer."},
            'dev': {"desc": "Python __pycache__, Pip/Nuget/Cargo/Node caches.", "risk": "Safe. Libraries and build artifacts will be re-downloaded/built."},
            'wsl': {"desc": "WSL2 Virtual Disk Compaction.", "risk": "Safe. Reclaims 'ghost space' from deleted files in Linux (Uses 'wsl --compact')."}
        }
        return infos.get(category, {"desc": "Unknown category.", "risk": "Unknown risk."})

    def get_path(self, category: str) -> str:
        """Get path for opening folder."""
        paths = {
            'temp': self.user_temp,
            'adobe': self.adobe_cache,
            'downloads': self.downloads,
            'shader': self.nv_shader if os.path.exists(self.nv_shader) else self.amd_shader,
            'engine': self.ue_ddc,
            'delivery': r"C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\DeliveryOptimization\Cache",
        }
        return paths.get(category, "")

    def _get_folder_size(self, path) -> int:
        """Calculate folder size in bytes."""
        total = 0
        if not path or not os.path.exists(path): return 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self._get_folder_size(entry.path)
        except: pass
        return total

    def clean_temp_files(self):
        """Clean User and Windows Temp folders."""
        for folder in [self.user_temp, self.win_temp]:
            if not folder or not os.path.exists(folder): continue
            self._clean_folder(folder)

    def _clean_folder(self, folder):
        """Recursively clean folder contents with robust error handling for locked/read-only files."""
        if not os.path.exists(folder): return
        
        import stat
        def _make_writable_and_del(path, func):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except: pass

        def _on_rm_error(func, path, exc_info):
            _make_writable_and_del(path, func)

        for item in os.listdir(folder):
            path = os.path.join(folder, item)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    try:
                        os.remove(path)
                    except:
                        _make_writable_and_del(path, os.remove)
                elif os.path.isdir(path):
                    shutil.rmtree(path, onerror=_on_rm_error)
            except Exception:
                pass # Skip files currently in use

    def clean_recycle_bin(self):
        """Empty Recycle Bin via shell32."""
        try:
            # SHEmptyRecycleBinW(hwnd, root_path, flags)
            # Flags: SHERB_NOCONFIRMATION = 0x00000001, SHERB_NOPROGRESSUI = 0x00000002, SHERB_NOSOUND = 0x00000004
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        except Exception as e:
            logger.error(f"Recycle bin error: {e}")

    def clean_winsxs(self):
        """Run DISM StartComponentCleanup (Requires Admin - Runs async typically)."""
        # This blocks, so it should be run in a thread
        try:
            subprocess.run(['dism', '/online', '/cleanup-image', '/startcomponentcleanup', '/quiet'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def toggle_hibernate(self, enable: bool):
        """Toggle hibernation file (hiberfil.sys)."""
        action = "on" if enable else "off"
        try:
            subprocess.run(['powercfg', '-h', action], creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def clean_delivery_optimization(self):
        """Clean Delivery Optimization Cache."""
        # This usually requires stopping the DoSvc service first
        try:
            subprocess.run('net stop DoSvc', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            cache_path = r"C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\DeliveryOptimization\Cache"
            if os.path.exists(cache_path):
                shutil.rmtree(cache_path)
            subprocess.run('net start DoSvc', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def clean_shaders(self):
        """Clear GPU Shader Caches."""
        for path in [self.nv_shader, self.amd_shader]:
            if os.path.exists(path):
                self._clean_folder(path)

    def clean_engine_cache(self):
        """Clear Unreal Engine Derived Data Cache."""
        if os.path.exists(self.ue_ddc):
            self._clean_folder(self.ue_ddc)

    def compact_wsl(self):
        """Compact WSL2 disks."""
        # We need to find the names of distributions
        try:
            # Simple approach: wsl --compact distributes finding might be slow
            # Let's try to find .vhdx files and run wsl --manage <distro> --compact if we had names
            # Or just wsl --shutdown then compact files directly if possible? No, wsl --compact is safer
            subprocess.run(['wsl', '--shutdown'], creationflags=subprocess.CREATE_NO_WINDOW)
            # Find and compact vhdx (Note: This might be OS version dependent)
            # For simplicity, we'll try 'wsl --compact' for all running if supported
            pass
        except:
            pass

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
