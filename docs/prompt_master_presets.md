# Prompt Master Presets (developer note)

Preset storage: `config/prompt_master_presets.json`

Top-level shape:
```json
{
  "<EngineName>": [
    {
      "name": "Preset Name",
      "input1": "Primary brief text",
      "input2": "Secondary details",
      "camera": "Default|Close-up|Wide|Aerial|POV",
      "style": "Neutral|Cinematic|Documentary|Anime|Realistic"
    }
  ]
}
```

Defaults seeded in code for `NanoBanana` (examples sourced from Nano Banana prompt guidelines):
- `NB - Product Hero`
- `NB - Scene Builder`
- `NB - Character Mood`

How to add more presets:
1. Edit `config/prompt_master_presets.json` manually following the above structure.
2. Or add via UI: select engine tab, fill Input1/2, choose camera/style, click Add (Save).
3. Presets are engine-specific; names must be unique per engine.

Fields:
- `name`: unique label per engine.
- `input1`, `input2`: freeform text blocks; used to build the prompt text.
- `camera`: maps to the camera dropdown.
- `style`: maps to the style dropdown.

Note: The app seeds defaults if the file is missing/empty. Delete entries to remove defaults. ***!
