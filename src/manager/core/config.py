import json
import logging
from pathlib import Path
from utils.config_builder import build_config

logger = logging.getLogger("manager.core.config")

class ConfigManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.config_path = root_dir / "config" / "menu_config.json"
        self._cache = None
        
    def load_config(self, force_reload=False) -> list:
        """Load menu configuration from JSON."""
        if self._cache is not None and not force_reload:
            return self._cache

        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    self._cache = json.load(f)
                    return self._cache
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
        return []

    def save_config(self, items: list, settings: dict) -> bool:
        """
        Save items to menu_config.json and split into category files.
        Regenerates the main config after saving categories.
        """
        try:
            # Group by category
            categories = {}
            for item in items:
                cat = item.get('category', 'Custom')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            # Write to category files
            cat_dir = self.root_dir / "config" / "menu_categories"
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            # Sync category colors if a category is deleted/renamed effectively
            # (Logic for cleaning up unused category files could go here, 
            # but currently we just overwrite existing known ones)
            
            for cat, cat_items in categories.items():
                # Sanitize filename
                safe_cat = "".join(x for x in cat if x.isalnum() or x in (' ', '_', '-')).strip()
                filename = f"{safe_cat.lower()}.json"
                file_path = cat_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cat_items, f, indent=4)
            
            # Regenerate main config using the builder utility
            # This ensures menu_config.json is a verified compilation of categories
            build_config() 
            
            # Update Cache
            self._cache = items # items is already the latest list provided by caller
            # Or invalidate
            # self._cache = None 
            
            logger.info("Config saved and synced to categories.")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def rename_group(self, items: list, old_name: str, new_name: str) -> int:
        """Rename a submenu group across all items."""
        count = 0
        for item in items:
            if item.get('submenu') == old_name:
                item['submenu'] = new_name
                count += 1
        return count

    def ungroup_items(self, items: list, group_name: str) -> int:
        """Move all items in a group to 'ContextUp' root."""
        count = 0
        for item in items:
            if item.get('submenu') == group_name:
                item['submenu'] = "ContextUp"
                count += 1
        return count
