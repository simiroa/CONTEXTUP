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
            self.config_path = root_dir / config_path
        else:
            self.config_path = path_obj
            
        self.items: List[Dict] = []
        self.load()

    def load(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.items = json.load(f)

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
