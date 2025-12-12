import json
import os
from pathlib import Path
from typing import List, Dict, Optional

class MenuConfig:
    def __init__(self, config_rel_path: str = "config/menu_categories"):
        # Resolve path relative to project root
        root_dir = Path(__file__).parent.parent.parent
        self.config_dir = root_dir / config_rel_path
            
        self.items: List[Dict] = []
        self.load()

    def load(self):
        """
        Loads configuration from config/menu_categories/*.json files.
        """
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config category directory not found: {self.config_dir}")

        self.items = []
        files = sorted(self.config_dir.glob("*.json"))
        
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
            if (item.get('scope') == scope or item.get('scope') == 'both')
        ]

    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        for item in self.items:
            if item.get('id') == item_id:
                return item
        return None
