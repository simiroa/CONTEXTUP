
import json
import sys

def check_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"OK: {path}")
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {path} - {e}")
        sys.exit(1)

check_json(r"c:\Users\HG\Documents\HG_context_v2\ContextUp\config\i18n\en.json")
check_json(r"c:\Users\HG\Documents\HG_context_v2\ContextUp\config\i18n\ko.json")
