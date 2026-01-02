# Development Guide

> [!NOTE]
> For AI Agents: Please read [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md) first.

## Project Structure
*   **`src/core`**: Core logic (Registry, Config, Menu, Paths).
*   **`src/features`**: Implementation modules for features (Categorized).
*   **`src/utils`**: Shared utilities (GUI, Explorer, Config Builder, etc.).
*   **`config/categories`**: Feature definition files (flattened).
*   **`config/categories/comfyui.json`**: ComfyUI tools (nested `features` list).
*   **`userdata`**: User-specific data and settings (Git Ignored).
*   **`tools`**: External tools and **Embedded Python Environment** (`tools/python`).
*   **`assets`**: Icons and other visual resources.
*   **`resources`**: AI Models/Weights and backup binaries.
*   **`dev`**: Developer scripts and verification tools.

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

### Step 3: Install Dependencies
Install packages into the **Embedded Environment**:
```powershell
ContextUp/tools/python/python.exe -m pip install <package>
```
Update `requirements.txt` accordingly.

### Step 4: Localization (i18n)
All user-facing text must be localized using `src.utils.i18n`.

1.  **Code Usage**:
    ```python
    from utils.i18n import t
    # Use dot-notation keys corresponding to JSON structure
    btn = ctk.CTkButton(self, text=t("my_feature_gui.start_button"))
    ```
2.  **Add Keys**: Update `config/i18n/en.json` (Required) and `ko.json` (Optional).
    ```json
    "my_feature_gui": {
        "title": "My Feature",
        "start_button": "Start"
    }
    ```

### Step 5: Define Configuration
Edit the JSON file in `config/categories/` (e.g., `image.json`).

```json
{
    "category": "Tools",
    "id": "my_feature",
    "name": "My Tool Name",
    "icon": "assets/icons/icon_my_tool.ico",
    "types": ".jpg;.png",        // filter
    "scope": "file",             // file, directory, background (folder bg), tray_only
    "enabled": true,
    "submenu": "ContextUp",
    "show_in_tray": true,
    "environment": "system",
    "dependencies": ["Pillow"],  // items from requirements.txt
    "external_tools": ["FFmpeg"],// binaries in tools/ or PATH
    "is_extension": true,
    "order": 900,
    "gui": true,
    "description": "Short description for Item Editor"
}
```

### Step 6: Register in Menu Dispatcher
**Crucial for Context Menu**: Even if configured in JSON, the `src/core/menu.py` dispatcher must know how to launch your script.

1.  Open `src/core/menu.py`.
2.  Locate `build_handler_map()`.
3.  Add your ID mapping:
    ```python
    "my_feature": lambda p, s=None: gui_popen([PYTHONW_EXE, str(src_dir / "features" / "image" / "my_feature_gui.py"), str(p)]),
    ```

For ComfyUI entries, edit `config/categories/comfyui.json` and add a new item under the `features` list with a `script` field (e.g., `src.features.comfyui.my_gui`).

### Step 7: Registry Refresh
Run `manager.bat` or use CLI to refresh the context menu:
```powershell
ContextUp\tools\python\python.exe ContextUp\manage.py register
```

### ComfyUI Feature Addendum
When adding new ComfyUI features, follow these rules to avoid tray/GUI breakage:

*   **Startup/Attach**: Use `ComfyUIService.ensure_running()` to attach or start. Do not call `ComfyUIManager.start()` directly from GUI code.
*   **Port/Status**: Read the active port from the service and pass it to the client (`client.set_active_port(port)`).
*   **Paths**: Prefer `COMFYUI_PATH` pointing to the ComfyUI folder (not a `.bat`). If a launcher is required, set `COMFYUI_USE_LAUNCHER=true`.
*   **GUI Layout**: BaseWindow uses `grid` on the root. Do not mix `pack` on the root window. If you need a status bar, use `grid`.
*   **Logs/Console**: ComfyUI console output must stay ASCII-safe (Windows cp949). Use `ComfyUIService.open_console()` to tail `logs/comfyui_server.log`.
*   **Tray Visibility**: For ComfyUI tools that should appear in tray, set `category: "Comfyui"` and `show_in_tray: true` in `config/categories/comfyui.json`.
*   **External Tool Flag**: Include `"external_tools": ["ComfyUI"]` to keep dependency checks consistent.
*   **Web UI Naming**: Use "Open Web UI" for the ComfyUI browser entry (script: `src.features.comfyui.open_dashboard`).

---

## 3. Verification & Debugging

### Icon Management

**1. Check Missing Icons**
Run verify script to find enabled features without enabled icons:
```powershell
python dev/scripts/check_missing_icons.py
```

**2. Generate Dummy Icons**
If you don't have a design, generate a placeholder arrow/text icon:
1. Edit `dev/scripts/generate_icons.py` and add your tool to `TOOLS`.
2. Run: `python dev/scripts/generate_icons.py`

**3. Generate AI Icons (Advanced)**
1. **Prompts**: `python dev/scripts/update_prompts_md.py`
2. **Generate**: `python dev/scripts/generate_icons_ai.py --target my_feature`

### Automated Checks
Run the screenshot tool to verify GUI appearance and load errors:
```powershell
python dev/scripts/capture_gui_screenshots.py --themes
```

### Common Issues
*   **Context Menu vs Tray**:
    *   **Context Menu**: Controlled by `src/core/menu.py`. You MUST add a handler there.
    *   **Tray Menu**: Controlled by `src/tray/launchers.py`. It usually auto-detects scripts, but check if manual mapping is needed.
*   **ImportError**:Check `sys.path` insertion at the top of the GUI script.
*   **Registry Not Updating**: Close any open Explorer windows or restart `explorer.exe`.
*   **`SubCommands` Error**: Ensure you are not manually creating `SubCommands` keys in the registry (fixed in v4.0.0).
