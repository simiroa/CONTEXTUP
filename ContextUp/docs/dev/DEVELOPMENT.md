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

**Use Shared UI Components** from `src/utils/`:

| 모듈 | 클래스/함수 | 용도 |
|-----|-----------|-----|
| `gui_lib.py` | `BaseWindow` | 표준 윈도우 (타이틀바, 아이콘, 테마 자동 적용) |
| `gui_lib.py` | `FileListFrame` | 파일 목록 스크롤 프레임 |
| `gui_lib.py` | `PremiumScrollableFrame` | 자동 스크롤바 숨김 프레임 |
| `gui_lib.py` | `ask_string_modern()` | 입력 다이얼로그 |
| `progress_gui.py` | `BatchProgressGUI` | 배치 작업 진행률 창 |
| `progress_gui.py` | `run_batch_gui()` | 배치 GUI 헬퍼 함수 |

**Example Usage**:
```python
from utils.gui_lib import BaseWindow, FileListFrame
from utils.progress_gui import BatchProgressGUI

class MyToolGUI(BaseWindow):
    def __init__(self, files):
        super().__init__(title="My Tool", width=600, height=500)
        self.add_header("My Feature")
        FileListFrame(self.content, files).pack(fill="x")
```

**Theme Rules**:
- Use `customtkinter`. Never hardcode colors (use tuples for light/dark).
- Theme JSON: `src/utils/theme_contextup.json`
- Constants: `THEME_BG`, `THEME_FG`, `THEME_BORDER` from `gui_lib.py`

### Step 3: Install Dependencies
Install packages into the **Embedded Environment**:
```powershell
ContextUp/tools/python/python.exe -m pip install <package>
```
Update `requirements.txt` accordingly.

### Step 3.5: Register in Install Script (Optional)
If your feature requires new packages, register them in `src/setup/install.py` so they are installed automatically.

**Package Groups** (Choose appropriate group):
| 그룹 | 변수명 | 적용 조건 |
|-----|-------|--------|
| **Core** | `BASE_CORE` | 항상 설치 (기본 패키지) |
| **Media** | `PKG_MEDIA` | Image/Video/Audio 카테고리 선택 시 |
| **Document** | `PKG_DOC` | Document 카테고리 선택 시 |
| **Utilities** | `PKG_TOOLS` | Utilities 카테고리 선택 시 |
| **AI** | `TIER2_AI_PACKAGES` | AI 기능 (Tier 2 이상) |

**Example**: Adding a package to Media group:
```python
# src/setup/install.py
PKG_MEDIA = [
    # ... existing packages ...
    "my-new-package",  # My Feature - Description
]
```

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
    "category": "Utilities",
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

### Step 8: Create Manual Documentation
Create a user manual for your feature in `docs/manuals/ko/`.

1.  **Create File**: `docs/manuals/ko/<feature_id>.md`
2.  **Follow Template**:
    ```markdown
    # Feature Name (한글 이름)

    ## 소개
    기능에 대한 간단한 설명.

    ## 주요 기능
    - 기능 1
    - 기능 2

    ## 사용법
    1. 파일/폴더 선택 후 우클릭
    2. **Category → Feature Name** 선택
    3. 옵션 설정
    4. 실행

    ## 의존성
    - 필요한 패키지/도구 나열
    ```
3.  **Link in FEATURES.md**: `docs/user/FEATURES.md`에 매뉴얼 링크 추가

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
