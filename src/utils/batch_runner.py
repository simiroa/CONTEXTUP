import os
import time
import hashlib
import tempfile
from pathlib import Path

def collect_batch_context(item_id: str, target_path: str, timeout: float = 0.2) -> list[Path] | None:
    """
    Coordinates multiple processes launched by Windows Context Menu into a single batch.
    Returns a list of Paths if this process is the 'leader'.
    Returns None if this process is a 'follower' (should exit).
    """
    try:
        target = Path(target_path).resolve()
        parent = target.parent
        
        # Unique key for this batch operation
        # Key = item_id + parent_folder
        key_str = f"{item_id}_{parent}".encode('utf-8')
        key = hashlib.md5(key_str).hexdigest()
        
        lock_dir = Path(tempfile.gettempdir()) / "CreatorTools_Locks"
        lock_dir.mkdir(exist_ok=True)
        
        lock_file = lock_dir / f"{key}.txt"
        
        # 1. Register myself
        # Use append mode. Windows file locking might prevent simultaneous writes, so we retry.
        start_time = time.time()
        registered = False
        while time.time() - start_time < 1.0: # 1s max to register
            try:
                with open(lock_file, "a", encoding="utf-8") as f:
                    f.write(f"{target}\n")
                registered = True
                break
            except PermissionError:
                time.sleep(0.01)
            except Exception:
                time.sleep(0.01)
                
        if not registered:
            # Failed to write? Just run alone to be safe.
            return [target]
            
        # 2. Wait for others to register
        time.sleep(timeout)
        
        # 3. Read and Determine Leader
        try:
            if not lock_file.exists():
                # Lock file gone? Leader already took it and deleted it.
                # I am a late follower.
                return None
                
            with open(lock_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
            # Deduplicate and Sort
            # We resolve all paths to ensure consistency
            paths = sorted(list(set([Path(p).resolve() for p in lines])))
            
            if not paths:
                return None
                
            # Leader is the first one alphabetically
            if target == paths[0]:
                # I am leader
                # Cleanup the lock file so latecomers don't get confused (or they just exit)
                try:
                    lock_file.unlink()
                except:
                    pass
                return paths
            else:
                # I am follower
                return None
                
        except Exception:
            # Error reading? Fallback to single run
            return [target]
            
    except Exception as e:
        # Fallback for any other error
        print(f"Batch runner error: {e}")
        return [Path(target_path)]
