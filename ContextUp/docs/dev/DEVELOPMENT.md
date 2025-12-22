# Development Guide

> [!NOTE]
> For AI Agents: Please read [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md) first.

## Project Structure
*   **`src/core`**: Core logic (Registry, Config, Menu, Paths).
*   **`src/features`**: Implementation modules for features (Categorized).
*   **`src/utils`**: Shared utilities (GUI, Explorer, Config Builder, etc.).
*   **`config/categories`**: Feature definition files (Flattened).
*   **`userdata`**: User-specific data and settings (Git Ignored).
*   **`tools`**: Helper scripts and **Embedded Python Environment** (`tools/python`).
*   **`assets`**: Icons and other visual resources.
*   **`resources`**: AI Models/Weights and backup binaries.
*   **`tools`**: External Tools (FFmpeg, Blender, Mayo, ComfyUI) and Python environment.

---

## 1. Feature Design & Ideation

Clarify the feature's purpose and placement.
*   **Utility**: Does this save time or solve a specific problem?
*   **Context**: Where should this appear? (File, Folder, background, or Tray?)
*   **Category**: Which existing category does it fit into? (image, video, ai, sequence, etc.)

---

## 2. Step-by-Step Implementation

### Step 1: Create Script & Path Management
Create your script in `src/features/<category>/`.

**CRITICAL: Use Centralized Paths**
Instead of hardcoding paths or using `os.path`, use `src.core.paths`.

```python
# --- Standard Header ---
import sys
from pathlib import Path

# Add src to path if running directly
ROOT = Path(__file__).resolve().parent
while not (ROOT / 'src').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
if (ROOT / 'src').exists() and str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

from core.paths import USERDATA_DIR, TOOLS_DIR
from utils.gui_lib import BaseWindow
# -----------------------
```

### Step 2: Implement GUI (Guidelines)
- **Theme**: Use `customtkinter`. Never hardcode colors (use tuples for light/dark).
- **Localization**: Update `config/i18n/en.json` and `ko.json`. Use `from utils.i18n import t`.

### Step 3: Install Dependencies
Install packages into the **Embedded Environment**:
```powershell
ContextUp/tools/python/python.exe -m pip install <package>
```
Update `requirements.txt` accordingly.

### Step 4: Define Configuration
Edit the JSON file in `config/categories/` (e.g., `image.json`).

```json
{
    "id": "my_feature",
    "name": "My Tool Name",
    "icon": "icon_my_tool.ico",
    "enabled": true,
    "show_in_context_menu": true,
    "show_in_tray": true,
    "scope": "file",            // file, directory, or background
    "types": ".jpg;.png",       // filter
    "environment": "system",    // or "conda"
    "dependencies": ["Pillow"], // items from requirements.txt
    "external_tools": ["FFmpeg"],// binaries in tools/ or PATH
    "description": "Short description for Item Editor",
    "script": "src.features.image.my_tool" // Module path
}
```

### Step 5: Registry Refresh
Run `manager.bat` or use CLI to refresh the context menu:
```powershell
ContextUp\tools\python\python.exe ContextUp\manage.py register
```

---

## 3. Verification & Debugging

### AI Icons
1. **Prompts**: `python dev/scripts/update_prompts_md.py`
2. **Generate**: `python dev/scripts/generate_icons_ai.py --target my_feature`

### Automated Checks
Run the screenshot tool to verify GUI appearance and load errors:
```powershell
python dev/scripts/capture_gui_screenshots.py --themes
```

### Common Issues
*   **ImportError**: Check `sys.path` insertion at the top of the GUI script.
*   **Registry Not Updating**: Close any open Explorer windows or restart `explorer.exe`.
*   **`SubCommands` Error**: Ensure you are not manually creating `SubCommands` keys in the registry (fixed in v4.0.0).
