# Development Guidelines

## Project Structure
-   **`src/core`**: Core logic (Registry, Config, Menu).
-   **`src/scripts`**: Implementation scripts for features.
-   **`src/utils`**: Shared utilities (GUI, Explorer, Config Builder, etc.).
-   **`config`**: Configuration files (`settings.json`).
-   **`config/menu_categories`**: Split definition files for menu items (Source of Truth).
-   **`tools`**: Helper scripts (`manage_icons.py`, `setup_tools.py`) and external binaries.
-   **`assets`**: Icons and other resources.

## Adding a New Feature

The project uses a **split configuration system** and **automated build tools**. Follow this process to add new features:

### 1. Create Script
Add your implementation script to `src/scripts/`.
-   Use `src.utils.image_utils.scan_for_images` for robust image handling/recognition.
-   Use `src.utils.explorer.get_selection_from_explorer` for generic batch file processing.
-   Use absolute imports for internal modules (e.g., `from core.logger import setup_logger`).

### 2. Define Configuration
**DO NOT edit `config/menu_config.json` directly.**
Instead, edit the appropriate JSON file in `config/menu_categories/` (e.g., `image.json`, `system.json`).

Add your item entry:
```json
{
    "category": "MyCategory",
    "id": "my_feature_name",
    "name": "My Feature Name",
    "icon": "assets/icons/icon_my_feature.ico",
    "types": ".jpg;.png",
    "scope": "file",
    "enabled": true,
    "submenu": "ContextUp",
    "order": 500,
    "gui": true,
    "dependencies": ["Pillow", "numpy"]
}
```

#### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `category` | ✅ | Category name (Image, Video, AI, System, etc.) |
| `id` | ✅ | **Unique ID matching name in snake_case** (e.g., `batch_rename`, `finder`). Used as reset source. |
| `name` | ✅ | Display name in context menu |
| `icon` | ✅ | Path to icon file |
| `types` | ✅ | File extensions (`;` separated) or `*` for all |
| `scope` | ✅ | `file`, `folder`, `directory`, `background`, or `items` |
| `enabled` | ✅ | `true` or `false` |
| `submenu` | ✅ | Always `"ContextUp"` |
| `order` | ✅ | Sort order (lower = higher position) |
| `gui` | ✅ | `true` if opens GUI window, `false` for instant execution |
| `dependencies` | ✅ | Array of required packages (empty `[]` if none) |
| `hotkey` | ❌ | Optional global hotkey (e.g., `<ctrl>+<alt>+v`) |
| `show_in_tray` | ❌ | Show in tray menu (`true`/`false`) |

### 3. Manage Icons
**Option A: Manual Icons**
If you have an `.ico` file, place it in `assets/icons/`.

**Option B: AI Generation (Recommended)**
1.  Add your icon prompt to `docs/user/ICONS.md`
2.  Run the generator:
    ```bash
    python tools/generate_icons_ai.py
    ```

### 4. Register Dispatcher
Update `src/core/menu.py`:
-   Add your `id` and handler function to the `build_handler_map()` dictionary.
-   Use `_lazy("module", "function")` for faster startup.

Example:
```python
"my_feature_name": _lazy("scripts.my_script", "my_function"),
```

### 5. Update Dependencies
If your script uses new libraries, add them to the appropriate requirements file:
-   **`requirements_core.txt`**: Standard dependencies (GUI, System).
-   **`requirements_ai.txt`**: Heavy AI dependencies (Conda environment).

### 6. Register in Windows
Apply changes to the Windows Registry:
```bash
python manage.py register
```

### 7. Verify
-   Check the Context Menu in Windows Explorer.
-   **CRITICAL**: Check `logs/debug.log` to confirm the feature is executing correctly.
-   (Optional) Run tests: `python manage.py test`.

### 8. Documentation
-   Update `docs/` to reflect the new feature.
-   If it's a visible feature, update `docs/user/USER_GUIDE.md`.

## Testing
-   Run `python manage.py test` to run automated tests.
-   Use `src/core/logger.py` for logging.

## Schema Notes

### Removed Fields
- `status`: No longer needed (all items are complete)
- `environment`: Unified to embedded Python

### New Fields
- `gui`: Indicates if feature opens a GUI window
- `dependencies`: Required packages for the feature

---

## Multi-File Selection Pattern (Batch Processing)

When users select multiple files in Explorer and invoke a context menu action, Windows launches **one process per file**. This can cause hundreds of GUI windows to open simultaneously. Use the following pattern to handle this correctly:

### Architecture

```
[User selects 100 files] → [Windows launches 100 processes]
          ↓
[Each process: Explorer COM → get ALL selected files instantly]
          ↓
[batch_runner mutex → only 1 process becomes "leader"]
          ↓
[Leader opens GUI with full file list, others exit]
```

### Implementation Template

```python
# === FAST STARTUP: Delay heavy imports ===
import sys
from pathlib import Path

current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))


def get_all_selected_files(anchor_path: str) -> list[Path]:
    """Get all selected files via Explorer COM - INSTANT for any file count."""
    try:
        from utils.explorer import get_selection_from_explorer
        selected = get_selection_from_explorer(anchor_path)
        if selected and len(selected) > 0:
            return selected
    except Exception:
        pass
    return [Path(anchor_path)]


def main():
    """Import heavy modules here, not at top level."""
    import customtkinter as ctk
    from PIL import Image
    # ... rest of imports
    
    class MyToolGUI(BaseWindow):
        def __init__(self, files_list):
            # files_list contains ALL selected files
            self.files = files_list
            # ...
    
    return MyToolGUI


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # STEP 1: Get ALL selected files instantly via Explorer COM
        all_files = get_all_selected_files(anchor)
        
        # STEP 2: Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("my_tool_id", anchor, timeout=0.2) is None:
            sys.exit(0)  # Another instance is handling this
        
        # STEP 3: Launch GUI with complete file list
        MyToolGUI = main()
        app = MyToolGUI(all_files)
        app.mainloop()
```

### Key Points

| Element | Purpose |
|---------|---------|
| `get_selection_from_explorer()` | Uses Explorer COM to get ALL selected files instantly |
| `collect_batch_context()` | Prevents multiple GUI windows (mutex) |
| Deferred imports | Faster startup by loading heavy modules later |
| `ThreadPoolExecutor` | For parallel processing of large batches |

### Thread Count Option

For batch processing tools, add a thread count option:
- `0` = Auto (use `multiprocessing.cpu_count()`)
- `1-16` = Fixed thread count

```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

threads = multiprocessing.cpu_count() if thread_count == 0 else thread_count

with ThreadPoolExecutor(max_workers=threads) as executor:
    results = list(executor.map(process_single_file, files))
```

