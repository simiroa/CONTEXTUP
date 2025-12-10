import os
import hashlib
import time
import re
from pathlib import Path
from typing import List, Callable, Optional, Dict
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import FinderGroup

def _get_file_hash(path, chunk_size=65536):
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def _get_partial_hash(path, chunk_size=4096):
    """
    Reads just the first few KB and last few KB to quickly filter non-duplicates.
    """
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            if size < chunk_size * 3:
                return _get_file_hash(path) # Just hash it all if small
            
            chunk_start = f.read(chunk_size)
            f.seek(-chunk_size, 2)
            chunk_end = f.read(chunk_size)
            return hashlib.md5(chunk_start + chunk_end).hexdigest()
    except:
        return ""

def scan_worker(target_path: Path, mode: str = "simple", criteria: Optional[Dict[str, bool]] = None, status_callback: Optional[Callable[[str], None]] = None) -> List[FinderGroup]:
    """
    Core scanning logic.
    mode: 'simple' or 'smart'
    criteria: dict with keys 'name', 'size', 'hash' (used in simple mode)
    """
    if criteria is None: criteria = {}
    
    if status_callback: status_callback("Indexing files...")
    
    path = Path(target_path)
    EXCLUDES = {'.git', 'node_modules', '__pycache__', '$RECYCLE.BIN', 'System Volume Information'}
    
    all_files = []
    
    # Optimized Walk
    count_walk = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        for f in files:
            all_files.append(Path(root) / f)
            count_walk += 1
            if count_walk % 5000 == 0:
                time.sleep(0.001) # Yield
    
    total_files = len(all_files)
    if status_callback: status_callback(f"Analyzing {total_files} files...")
    
    groups_data = {} 
    
    if mode == "simple":
        # Criteria: name, size, hash
        use_name = criteria.get('name', True)
        use_size = criteria.get('size', True)
        use_hash = criteria.get('hash', False)
        
        # 1. Group by "Cheap" criteria (Name/Size)
        pre_groups = defaultdict(list)
        for i, f in enumerate(all_files):
            if i % 2000 == 0: time.sleep(0.001)
            
            key_parts = []
            try:
                if use_name: key_parts.append(f.name)
                if use_size: key_parts.append(f.stat().st_size)
            except OSError: continue
            
            if not key_parts: 
                # If nothing selected, maybe group everything? No, unsafe.
                # Default to Name if nothing selected?
                key_parts.append(f.name)
                
            pre_groups[tuple(key_parts)].append(f)
            
        # Filter candidates (len > 1)
        candidates = [flist for flist in pre_groups.values() if len(flist) > 1]
        
        # 2. If Hash requested, sub-group these candidates
        if use_hash:
            total_groups = len(candidates)
            processed_groups = 0
            
            def process_hash_group(flist):
                # Optimization: Partial Hash first
                partial_map = defaultdict(list)
                for f in flist:
                    try:
                        ph = _get_partial_hash(f)
                        partial_map[ph].append(f)
                    except OSError: pass
                
                final_map = defaultdict(list)
                for ph, sublist in partial_map.items():
                    if len(sublist) < 2: 
                        continue # Unique partial hash -> Unique file
                        
                    # Collision in partial hash -> Do Full Hash
                    for f in sublist:
                        try:
                            h = _get_file_hash(f)
                            final_map[h].append(f)
                        except OSError: pass
                        
                return final_map

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(process_hash_group, c): c for c in candidates}
                for fut in as_completed(futures):
                    processed_groups += 1
                    if status_callback and processed_groups % 10 == 0:
                        status_callback(f"Hashing groups: {processed_groups}/{total_groups}")
                    
                    try:
                        result_map = fut.result()
                        for h, files in result_map.items():
                            if len(files) > 1:
                                groups_data[f"HASH: {h[:8]}..."] = files
                    except Exception: pass
        else:
            # Just return the name/size matches
            for key, files in pre_groups.items():
                if len(files) > 1:
                    # Construct a group name
                    name_str = " | ".join(map(str, key))
                    groups_data[f"Match: {name_str}"] = files

    elif mode == "smart":
        pattern = re.compile(r"^(.*?)[-_ .]*(?:v|V)?(\d+)[-_ .]*(\.[a-zA-Z0-9]+)$")
        raw_groups = defaultdict(list)
        
        count = 0
        # Analyze filenames
        for f in all_files:
            count += 1
            if count % 1000 == 0:
                 if status_callback: status_callback(f"Matching names: {count}/{total_files}...")
                 time.sleep(0.001) # Yield to UI
                 
            try:
                match = pattern.match(f.name)
                if match:
                    base, ver, ext = match.groups()
                    if not base: base = "root"
                    
                    key = (str(f.parent), base.lower(), ext.lower())
                    raw_groups[key].append(f)
            except Exception: pass
        
        # Heuristic Analysis
        total_raw = len(raw_groups)
        processed_raw = 0
        
        if status_callback: status_callback(f"Grouping {total_raw} sets...")
        
        for key, flist in raw_groups.items():
            processed_raw += 1
            if processed_raw % 500 == 0:
                time.sleep(0.001)
                
            if len(flist) < 2: continue
            
            is_sequence = False
            if len(flist) > 12: is_sequence = True
            else:
                try:
                    match = pattern.match(flist[0].name)
                    if match and len(match.group(2)) >= 3:
                        is_sequence = True
                except: pass
                    
            group_type = "SEQ" if is_sequence else "VER"
            base_name = Path(key[0]).name + "/" + key[1]
            
            if is_sequence:
                flist.sort(key=lambda x: x.name)
            else:
                try:
                    flist.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                except: pass
            
            groups_data[f"{group_type}: {base_name}"] = flist

    # Convert to FinderGroup objects
    final_groups = []
    for name, flist in groups_data.items():
        # strict sort by name/timestamp is handled above or here
        if "HASH:" in name: flist.sort()
        
        grp = FinderGroup(name, flist)
        final_groups.append(grp)
        
    # Sort groups by name (or count?)
    final_groups.sort(key=lambda x: x.name)
    
    if status_callback: status_callback("Ready.")
    return final_groups
