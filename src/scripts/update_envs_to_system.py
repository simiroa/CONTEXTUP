import json
from pathlib import Path

files = [
    "config/tools/ai_inpaint.json",
    "config/tools/ai_maketile.json",
    "config/tools/ai_outpaint.json",
    "config/tools/ai_pbr_gen.json",
    "config/tools/ai_style_change.json",
    "config/tools/ai_to_prompt.json",
    "config/tools/ai_weathering.json",
    "config/tools/image_remove_bg_ai.json",
    "config/tools/image_upscale_ai.json",
    "config/tools/sys_clipboard_ai.json",
    "config/tools/video_frame_interp.json"
]

root = Path(__file__).parent.parent.parent

for f in files:
    path = root / f
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if data.get("environment") == "ai":
                data["environment"] = "system"
                
                with open(path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4)
                print(f"Updated {f}")
        except Exception as e:
            print(f"Error updating {f}: {e}")
    else:
        print(f"File not found: {f}")
