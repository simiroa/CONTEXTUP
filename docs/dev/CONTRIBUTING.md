# Development Guidelines & Best Practices

## 1. Registry & Context Menu
*   **Unified Menu Key**: Always register tools under a single main key (e.g., `HKCU\Software\Classes\*\shell\CreatorTools_v2`) to prevent menu fragmentation.
*   **Visibility Control**: Use the `AppliesTo` registry value to filter visibility based on file extensions or properties (e.g., `System.FileExtension:=.jpg OR System.FileExtension:=.png`). Avoid creating separate keys for every file type.
*   **Scope Management**:
    *   `Files`: Register under `*`.
    *   `Folders`: Register under `Directory`.
    *   `Background`: Register under `Directory\Background`.
    *   **Avoid Duplicates**: Do not register the same tool under multiple keys if `AppliesTo` can handle it, unless specifically required for different contexts (e.g., Folder vs Background).
*   **Cleanup**: Always provide a cleanup script (`tools/cleanup_registry.py`) to remove old keys before registering new ones to prevent "phantom" items.

## 2. Tool Implementation Patterns
*   **Batch Processing by Default**:
    *   Tools should always handle **multiple selected files**.
    *   Use `utils.explorer.get_selection_from_explorer(target_path)` to retrieve the full selection.
    *   If `target_path` is the only argument, fallback to treating it as a single item list.
    *   **Loop & Report**: Iterate through the selection, collect success/errors, and show a **single summary** at the end (e.g., "Converted 5/5 files"). Do not show a popup for every single file.
*   **GUI & Interaction**:
    *   **Focus**: Always force the root window to focus (`root.attributes("-topmost", True)`, `root.lift()`) to prevent dialogs from appearing behind Explorer.
    *   **Consolidated Dialogs**: For tools requiring input (e.g., "Sequence to Video"), show a single dialog gathering all parameters (FPS, Codec, etc.) upfront, rather than a chain of popups.
*   **Dispatching**:
    *   Ensure every new tool ID in `menu_config.json` has a corresponding handler in `src/core/menu.py`.
    *   Missing handlers cause silent failures (script exits immediately).

## 3. Python & Environment
*   **Embedded Python**: The extension runs in an embedded environment. Do not rely on global `pip` packages unless they are installed in the embedded environment's site-packages.
*   **Imports**: Use absolute imports from `src` (e.g., `from core.logger import ...`). Ensure `sys.path` includes the project root.

## 4. Iconography
*   **Consistency**: Use a standard set of icons located in `assets/icons`.
*   **Formats**: Windows Registry prefers `.ico` files.

## 5. Troubleshooting Checklist
*   **"Tool doesn't appear"**: Check `AppliesTo` logic and Registry path.
*   **"Tool does nothing"**: Check `menu.py` dispatch logic and `logs/menu_dispatcher.log`.
*   **"Dialog not showing"**: Check window focus/topmost settings.
*   **"Only processes one file"**: Check if the script uses `get_selection_from_explorer`.
