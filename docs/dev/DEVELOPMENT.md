# Development Guidelines

## Project Structure
-   **`src/core`**: Core logic (Registry, Config, Menu).
-   **`src/scripts`**: Implementation scripts for features.
-   **`src/utils`**: Shared utilities (GUI, Explorer, etc.).
-   **`config`**: Configuration files (`menu_config.json`, `settings.json`).
-   **`libs`**: External libraries and addons.
-   **`assets`**: Icons and other resources.

## Adding a New Feature
1.  **Create Script**: Add your python script to `src/scripts/`.
2.  **Update Config**: Add an entry to `config/menu_config.json`.
    ```json
    {
        "category": "MyCategory",
        "id": "my_feature_id",
        "name": "My Feature Name",
        "icon": "assets/icons/icon_my_feature.ico",
        "types": "*",
        "scope": "file",
        "status": "COMPLETE"
    }
    ```
3.  **Register**: Run `python manage.py register` to update the Windows Registry.

## Testing
-   Run `python manage.py test` to run automated tests.
-   Use `src/core/logger.py` for logging.

## Migration from v1
-   This version uses a **Registry-based** approach, not a console launcher.
-   All menu items are defined in `menu_config.json`.
-   `manage.py` is the central command-line tool.
