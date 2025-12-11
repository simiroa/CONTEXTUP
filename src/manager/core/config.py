import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("manager.core.config")

class ConfigManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.categories_dir = root_dir / "config" / "menu_categories"
        self._cache = None
        self._last_load_time = None  # Timestamp of last load
        
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
            self._last_load_time = time.time()  # Record load time
            return items
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return []

    def validate_unique_ids(self, items: list) -> tuple:
        """
        Check for duplicate IDs across all items.
        Returns (is_valid, duplicate_ids).
        """
        seen = {}
        duplicates = []
        for item in items:
            item_id = item.get('id')
            if not item_id:
                continue
            if item_id in seen:
                if item_id not in duplicates:
                    duplicates.append(item_id)
            else:
                seen[item_id] = item
        return (len(duplicates) == 0, duplicates)

    def is_cache_stale(self) -> bool:
        """
        Check if any config file changed since last load.
        Returns True if external changes detected.
        """
        if self._cache is None or self._last_load_time is None:
            return True
        try:
            for fpath in self.categories_dir.glob("*.json"):
                if fpath.stat().st_mtime > self._last_load_time:
                    logger.info(f"External change detected: {fpath.name}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking file timestamps: {e}")
            return True
        return False

    def cleanup_empty_files(self) -> list:
        """
        Remove empty category JSON files.
        Returns list of removed filenames.
        """
        removed = []
        try:
            for fpath in self.categories_dir.glob("*.json"):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if not data or (isinstance(data, list) and len(data) == 0):
                        fpath.unlink()
                        removed.append(fpath.name)
                        logger.info(f"Removed empty file: {fpath.name}")
                except Exception as e:
                    logger.warning(f"Error checking {fpath.name}: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        return removed

    def save_config(self, items: list, settings: dict) -> tuple:
        """
        Save items directly to menu_categories/*.json files.
        One file per category.
        
        Returns (success: bool, message: str)
        """
        # 1. Validate unique IDs before saving
        is_valid, duplicates = self.validate_unique_ids(items)
        if not is_valid:
            msg = f"Duplicate IDs found: {', '.join(duplicates)}"
            logger.error(msg)
            return (False, msg)
        
        try:
            # 2. Group by category
            categories = {}
            for item in items:
                cat = item.get('category', 'Custom')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            self.categories_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Write to category files
            written_files = set()
            for cat, cat_items in categories.items():
                # Sanitize filename
                safe_cat = "".join(x for x in cat if x.isalnum() or x in (' ', '_', '-')).strip()
                if not safe_cat: safe_cat = "Custom"
                filename = f"{safe_cat.lower()}.json"
                file_path = self.categories_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cat_items, f, indent=4)
                written_files.add(filename)
            
            # 4. Cleanup empty files (categories that no longer have items)
            removed = self.cleanup_empty_files()
            
            # 5. Update Cache
            self._cache = items
            self._last_load_time = time.time()
            
            msg = f"Saved {len(items)} items to {len(written_files)} files."
            if removed:
                msg += f" Cleaned up: {', '.join(removed)}"
            logger.info(msg)
            return (True, msg)
            
        except Exception as e:
            msg = f"Error saving config: {e}"
            logger.error(msg)
            return (False, msg)

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
