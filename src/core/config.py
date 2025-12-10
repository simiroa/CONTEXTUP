import json
import os
from pathlib import Path
from typing import List, Dict, Optional

class MenuConfig:
    def __init__(self, config_path: str = "config/menu_config.json"):
        # Resolve path relative to project root if it's not absolute
        path_obj = Path(config_path)
        if not path_obj.is_absolute():
            # This file is in src/core/, so root is 2 levels up
            root_dir = Path(__file__).parent.parent.parent
            candidate = root_dir / config_path
            if candidate.exists():
                self.config_path = candidate
            else:
                # Fallback: if caller passed "menu_config.json", search under config/
                alt = root_dir / "config" / path_obj.name
                self.config_path = alt
        else:
            self.config_path = path_obj
            
        self.items: List[Dict] = []
        self.load()

    def load(self):
        """
        Loads configuration from config/menu_categories/*.json files.
        """
        # Determine config directory based on self.config_path
        # If config_path points to menu_config.json, we look for sibling 'menu_categories'
        if self.config_path.name == "menu_config.json":
            search_dir = self.config_path.parent / "menu_categories"
        elif self.config_path.is_dir():
            search_dir = self.config_path
        else:
            search_dir = self.config_path.parent

        if not search_dir.exists():
             # Fallback logic
             root_dir = Path(__file__).parent.parent.parent
             search_dir = root_dir / "config" / "menu_categories"

        if not search_dir.exists():
            # If even fallback fails, we might just be in a weird state, but let's try not to crash hard
            # or maybe we should raise error?
            # User explicitly requested folder loading, so error is appropriate.
            raise FileNotFoundError(f"Config category directory not found: {search_dir}")

        self.items = []
        files = sorted(search_dir.glob("*.json"))
        
        for json_file in files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.items.extend(data)
                    else:
                        pass 
            except Exception as e:
                print(f"Error loading {json_file.name}: {e}")

    def get_items_by_scope(self, scope: str) -> List[Dict]:
        """
        Get items that match the scope (file, folder, or both).
        """
        return [
            item for item in self.items 
            if item.get('status') == 'COMPLETE' and 
            (item.get('scope') == scope or item.get('scope') == 'both')
        ]

    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        for item in self.items:
            if item.get('id') == item_id:
                return item
        return None
