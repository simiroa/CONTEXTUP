
import json
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_keys(data, parent_key=''):
    keys = set()
    for k, v in data.items():
        current_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            keys.update(get_all_keys(v, current_key))
        else:
            keys.add(current_key)
    return keys

def compare_locale_files(en_path, ko_path):
    print(f"Comparing {en_path} and {ko_path}...")
    try:
        en_data = load_json(en_path)
        ko_data = load_json(ko_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    en_keys = get_all_keys(en_data)
    ko_keys = get_all_keys(ko_data)

    missing_in_ko = en_keys - ko_keys
    missing_in_en = ko_keys - en_keys

    print(f"Total keys in EN: {len(en_keys)}")
    print(f"Total keys in KO: {len(ko_keys)}")

    if missing_in_ko:
        print("\nKeys missing in KO:")
        for k in sorted(missing_in_ko):
            print(f"  - {k}")
    else:
        print("\nNo keys missing in KO.")

    if missing_in_en:
        print("\nKeys missing in EN (extra in KO):")
        for k in sorted(missing_in_en):
            print(f"  - {k}")
    else:
        print("\nNo keys missing in EN.")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    en_file = base_dir / "en.json"
    ko_file = base_dir / "ko.json"
    compare_locale_files(en_file, ko_file)
