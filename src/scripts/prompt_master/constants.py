import os


# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PRESETS_DIR = os.path.join(BASE_DIR, "config", "prompt_master", "presets")
TAGS_FILE = os.path.join(BASE_DIR, "config", "prompt_master", "tags", "global_tags.json")
TAG_CATEGORIES_FILE = os.path.join(BASE_DIR, "config", "prompt_master", "tags", "tag_categories.json")

# Engine color themes (for tabs)
ENGINE_COLORS = {
    "Flux": ("#9B59B6", "#8E44AD"),
    "Midj": ("#E74C3C", "#C0392B"),
    "Veo3": ("#3498DB", "#2980B9"),
    "nanobanana": ("#F39C12", "#E67E22"),
    "custom": ("#95A5A6", "#7F8C8D")
}
