# Development Guidelines

## Project Structure
-   **`src/core`**: Core logic (Registry, Config, Menu).
-   **`src/scripts`**: Implementation scripts for features.
-   **`src/utils`**: Shared utilities (GUI, Explorer, Config Builder, etc.).
-   **`config`**: Configuration files (`menu_config.json`, `settings.json`).
-   **`config/menu_categories`**: Split definition files for menu items (Source of Truth).
-   **`tools`**: Helper scripts (`manage_icons.py`, `setup_tools.py`) and external binaries.
-   **`assets`**: Icons and other resources.

## Adding a New Feature

The project uses a **split configuration system** and **automated build tools**. Follow this process to add new features:

### 1. Create Script
Add your implementation script to `src/scripts/`.
-   Use `src.utils.explorer.get_selection_from_explorer` for batch file processing.
-   Use absolute imports for internal modules (e.g., `from core.logger import setup_logger`).

### 2. Define Configuration
**DO NOT edit `config/menu_config.json` directly.**
Instead, edit the appropriate JSON file in `config/menu_categories/` (e.g., `image.json`, `system.json`).

Add your item entry:
```json
{
    "category": "MyCategory",
    "id": "my_feature_id", // Standard: [category_prefix]_[action] (e.g., img_resize, file_move)
    "name": "My Feature Name", // This is the generic display name
    "icon": "assets/icons/icon_my_feature.ico",
    "types": ".jpg;.png",  // or "*"
    "scope": "file",       // "file", "folder", "directory" (no background), "background", or "items" (file+dir)
    "status": "COMPLETE",
    "environment": "system", // or "embedded"
    "order": 500           // CRITICAL: Controls sort order in Context Menu (Lower = Top). Windows sorts by this prefix.
}
```

### 3. Build Configuration
Run the builder script to merge category files into the main config:
```bash
python src/utils/config_builder.py
```

### 4. Manage Icons
If you specified a new icon path, generate a dummy icon or verify existing ones:
```bash
python tools/manage_icons.py
```
This will create a placeholder icon at the specified path if it doesn't exist.

### 5. Register Dispatcher
Update `src/core/menu.py`:
-   Add your `id` and handler function to the `build_handler_map()` dictionary.
-   Use `_lazy("module", "function")` for faster startup.

### 6. Update Dependencies
If your script uses new libraries, add them to the appropriate requirements file:
-   **`requirements_core.txt`**: Standard dependencies (GUI, System).
-   **`requirements_ai.txt`**: Heavy AI dependencies (Conda environment).

### 7. Register in Windows
Apply changes to the Windows Registry. This works for new items, **name changes**, and **re-ordering**:
```bash
python apply_registry_changes.py
```
*Note: The script automatically handles unregistering old keys and registering new ones with the correct sort prefixes.*

### 8. Verify
-   Check the Context Menu in Windows Explorer.
-   Run the tool and check `debug.log`.
-   (Optional) Run tests: `python manage.py test`.

## Testing
-   Run `python manage.py test` to run automated tests.
-   Use `src/core/logger.py` for logging.

## Migration from v1
-   This version uses a **Registry-based** approach, not a console launcher.
-   Menu items are defined in `menu_categories/*.json` and built into `menu_config.json`.
-   `manage.py` is the central command-line tool.
