import json
import logging
from pathlib import Path
from pathlib import Path

logger = logging.getLogger("manager.core.config")

class ConfigManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.categories_dir = root_dir / "config" / "menu_categories"
        self._cache = None
        
    def load_config(self, force_reload=False) -> list:
        """Load menu configuration from menu_categories/*.json files."""
        if self._cache is not None and not force_reload:
            return self._cache

        items = []
        try:
            if not self.categories_dir.exists():
                logger.warning(f"Categories dir not found: {self.categories_dir}")
                return []
                
            files = sorted(self.categories_dir.glob("*.json"))
            for fpath in files:
                try:
                    with open(fpath, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            items.extend(data)
                except Exception as e:
                    logger.error(f"Error loading {fpath.name}: {e}")
                    
            self._cache = items
            return items
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return []

    def save_config(self, items: list, settings: dict) -> bool:
        """
        Save items directly to menu_categories/*.json files.
        One file per category.
        """
        try:
            # Group by category
            categories = {}
            for item in items:
                cat = item.get('category', 'Custom')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            self.categories_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to category files
            for cat, cat_items in categories.items():
                # Sanitize filename
                safe_cat = "".join(x for x in cat if x.isalnum() or x in (' ', '_', '-')).strip()
                if not safe_cat: safe_cat = "Custom"
                filename = f"{safe_cat.lower()}.json"
                file_path = self.categories_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cat_items, f, indent=4)
            
            # Update Cache
            self._cache = items 
            
            logger.info("Config saved to categories.")
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
