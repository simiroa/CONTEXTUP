import sys
from pathlib import Path
from PIL import Image

# Add src to path if needed (though usually imported from scripts)
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.explorer import get_selection_from_explorer

def scan_for_images(target=None, recursive=False):
    """
    Scans for images based on a target path (file or directory) or selection.
    
    Args:
        target: str or Path, or list of strings/Paths. The starting point.
        recursive: bool, whether to scan directories recursively (default False for safety).
        
    Returns:
        tuple(list[Path], int): (List of valid image Paths, Count of total candidates checked)
    """
    candidates = set()
    
    # 1. Normalize Input
    if target:
        if isinstance(target, (list, tuple)):
            for t in target:
                candidates.add(Path(t))
        else:
            p = Path(target)
            candidates.add(p)
            # Try to get explorer selection if it matches target context
            try:
                # Only check explorer if target looks like a path passed from context menu
                sel = get_selection_from_explorer(str(p))
                if sel:
                    for s in sel: candidates.add(Path(s))
            except:
                pass
    
    valid_files = []
    # Extensions to fast-accept without opening (unless corrupt, but we assume file extension trust mostly)
    # Added .jfif, .svg (maybe? PIL supports some), .webp
    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.tga', '.ico', '.exr', '.jfif'}
    
    checked_count = 0
    
    # Process candidates
    # We use a list to iterate because we might add more candidates (dir contents)
    # But actually we should just process the initial set and expand dirs
    
    initial_candidates = list(candidates)
    processed_paths = set()
    
    for p in initial_candidates:
        if not p.exists(): continue
        
        if p.is_dir():
            # Expand Directory
            # Use iterdir() for non-recursive or rglob defined by recursive flag
            iterator = p.rglob('*') if recursive else p.iterdir()
            
            for f in iterator:
                if f.is_file():
                    processed_paths.add(f)
                    if f.suffix.lower() in valid_exts:
                        valid_files.append(f)
                    # We usually don't deep-check every file in a folder for speed, 
                    # relying on extensions for bulk scan is standard.
        else:
            processed_paths.add(p)
            checked_count += 1
            # File Check
            # 1. Fast Check
            if p.suffix.lower() in valid_exts:
                valid_files.append(p)
            else:
                # 2. Deep Check (PIL) for files without standard extensions
                try:
                    with Image.open(p) as img:
                        img.verify()
                    valid_files.append(p)
                except:
                    pass
                    
    return sorted(list(set(valid_files))), len(processed_paths)
