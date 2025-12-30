import sys
import subprocess
import os
import urllib.request
import tarfile
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).parent.parent.parent  # src/scripts/install_contextup.py -> ROOT
TOOLS_DIR = ROOT_DIR / "tools"
PYTHON_DIR = TOOLS_DIR / "python"
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

# User data paths (in userdata/ directory)
USERDATA_DIR = ROOT_DIR / "userdata"
PROFILE_FILE = USERDATA_DIR / "install_profile.json"
USER_OVERRIDES = USERDATA_DIR / "user_overrides.json"

# App config paths
TIERS_FILE = ROOT_DIR / "config" / "install_tiers.json"

# IndyGreg Python Build Standalone 3.11.9 (Shared Install Only) with tkinter support
PYTHON_URL = "https://github.com/indygreg/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
PYTHON_ARCHIVE_NAME = "python-standalone.tar.gz"
SAFE_TEST_ENV = "CONTEXTUP_SAFE_TEST"

# ============================================================
# 移댄뀒怨좊━ 遺꾨쪟
# ============================================================

# ??긽 ?ㅼ튂?섎뒗 湲곕낯 移댄뀒怨좊━ (?ъ슜?먭? ?좏깮?섏? ?딆븘???먮룞 ?ы븿)
CORE_CATEGORIES = ["System", "Rename", "Clipboard", "Document"]

# ?ъ슜?먭? ?좏깮 媛?ν븳 ?듭뀡 移댄뀒怨좊━
OPTIONAL_CATEGORIES = {
    "Image": "?대?吏 ?몄쭛 (?뺤떇 蹂?? 由ъ궗?댁쫰, ?뚰꽣留덊겕 ??",
    "Video": "鍮꾨뵒??泥섎━ (蹂?? ?먮Ⅴ湲? GIF ?앹꽦) - FFmpeg ?꾩슂",
    "Audio": "?ㅻ뵒???몄쭛 (蹂?? 蹂쇰ⅷ 議곗젅) - FFmpeg ?꾩슂",
    "3D": "3D ?꾧뎄 (紐⑤뜽 蹂?? 由щ찓??",
    "Tools": "?좏떥由ы떚 (踰덉뿭湲???",
    "Sequence": "?쒗???꾧뎄 (?대?吏 ?쒗??愿由? 鍮꾨뵒??蹂??",
    "ComfyUI": "ComfyUI ?듯빀 (?앹꽦??AI) - ComfyUI ?ㅼ튂 ?꾩슂",
}

# ============================================================
# ?⑦궎吏 洹몃９
# ============================================================

# 湲곕낯 ?듭떖 ?⑦궎吏 (??긽 ?ㅼ튂)
BASE_CORE = [
    "customtkinter",
    "psutil",
    "pystray",
    "packaging",
    "pywin32",
    "requests",
    "pynput",
    "keyboard",
    "send2trash",
    "piexif",
    "pyperclip",
    "xxhash",
    "Pillow",
    "numpy<2",
    "tqdm",
]

# 誘몃뵒???몄쭛???⑦궎吏 (Image/Video/Audio ?좏깮 ??
PKG_MEDIA = [
    "ffmpeg-python",
    "imageio",
    "OpenEXR",
    "scipy",
    "rawpy",
    "pillow-heif",
    "opencv-python",
]

# 臾몄꽌 泥섎━ ?⑦궎吏
PKG_DOC = ["pypdf", "PyPDF2", "pdf2image", "pdf2docx", "pymupdf4llm", "svglib", "reportlab"]

# ?좏떥由ы떚 ?⑦궎吏
PKG_TOOLS = ["deep-translator", "yt-dlp"]

# 3D ?⑦궎吏
PKG_3D = ["pymeshlab"]


# AI Light: API 湲곕컲 (媛踰쇱?, ~100MB)
PKG_AI_LIGHT = [
    "google-generativeai",
    "google-genai",
    "ollama",
]

# AI Heavy: 濡쒖뺄 紐⑤뜽 (臾닿굅?, ~8-10GB)
PKG_AI_HEAVY = [
    "rembg",
    "accelerate",
    "diffusers",
    "transformers",
    "huggingface_hub",
    "torch --index-url https://download.pytorch.org/whl/cu121",
    "torchvision --index-url https://download.pytorch.org/whl/cu121",
    "torchaudio --index-url https://download.pytorch.org/whl/cu121",
    "open_clip_torch",
    "faster-whisper",
    "demucs",
    "gfpgan",
    "basicsr",
    "realesrgan",
    "kornia",
]


def migrate_userdata():
    """
    Migrate user data files from legacy config/ location to userdata/.
    Called during installation to preserve existing user settings.
    """
    config_dir = ROOT_DIR / "config"
    migrations = [
        (config_dir / "secrets.json", USERDATA_DIR / "secrets.json"),
        (config_dir / "user_overrides.json", USER_OVERRIDES),
        (config_dir / "gui_states.json", USERDATA_DIR / "gui_states.json"),
        (config_dir / "copy_my_info.json", USERDATA_DIR / "copy_my_info.json"),
        (config_dir / "install_profile.json", PROFILE_FILE),
        (config_dir / "download_history.json", USERDATA_DIR / "download_history.json"),
        (config_dir / "runtime" / "gui_states.json", USERDATA_DIR / "gui_states.json"),
        (config_dir / "runtime" / "download_history.json", USERDATA_DIR / "download_history.json"),
    ]
    
    USERDATA_DIR.mkdir(exist_ok=True)
    migrated = []
    
    for old_path, new_path in migrations:
        if old_path.exists() and not new_path.exists():
            try:
                shutil.move(str(old_path), str(new_path))
                migrated.append(old_path.name)
            except Exception as e:
                print(f"[WARN] 留덉씠洹몃젅?댁뀡 ?ㅽ뙣 {old_path.name}: {e}")
    
    if migrated:
        print(f"[INFO] ?ъ슜???곗씠??留덉씠洹몃젅?댁뀡 ?꾨즺: {', '.join(migrated)}")
    
    return migrated


def prompt_yn(message: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    choice = input(f"{message} {suffix}: ").strip().lower()
    if not choice:
        return default_yes
    return choice.startswith("y")


def download_file(url: str, dest: Path) -> bool:
    print(f"Downloading {url} -> {dest.name}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False


def extract_tar_gz(tar_path: Path, dest_dir: Path) -> bool:
    print(f"Extracting {tar_path.name} ...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
        return True
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return False


def _python_ok(py_exe: Path) -> bool:
    if not py_exe.exists():
        return False
    try:
        out = subprocess.check_output([str(py_exe), "-c", "import sys;print(sys.version.split()[0])"], text=True).strip()
        tk_ok = subprocess.call([str(py_exe), "-c", "import tkinter"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        return bool(out) and tk_ok
    except Exception:
        return False


def detect_existing_python():
    # Only return embedded python if checks pass
    embedded = PYTHON_DIR / "python.exe"
    if _python_ok(embedded):
        return [embedded]
    return []


def setup_embedded_python(force_reinstall: bool = False) -> Optional[Path]:
    py_exe = PYTHON_DIR / "python.exe"
    
    if not force_reinstall and _python_ok(py_exe):
        print(f"Using embedded Python: {py_exe}")
        return py_exe

    print("[INFO] Embedded Python not found or invalid.")
    print(f"Downloading standalone Python environment...")
    
    PYTHON_DIR.parent.mkdir(parents=True, exist_ok=True)
    tar_path = TOOLS_DIR / PYTHON_ARCHIVE_NAME
    
    if download_file(PYTHON_URL, tar_path):
        print("Download complete. Extracting...")
        # Create python directory if not exists
        if not extract_tar_gz(tar_path, TOOLS_DIR):
             print("[ERROR] Failed to extract Python archive.")
             return None
        
        # Cleanup tar
        try:
            os.remove(tar_path)
        except:
            pass
            
        # Verify again
        if _python_ok(py_exe):
            print(f"[SUCCESS] Embedded Python installed: {py_exe}")
            return py_exe
    else:
        print("[ERROR] Failed to download Python archive.")

    return None


def install_packages(py_exe: Path, categories: dict[str, bool]) -> bool:
    """
    Install packages per selected categories.
    """
    def run_pip(args):
        if args and args[0] == "install" and "--no-warn-script-location" not in args:
            args = list(args) + ["--no-warn-script-location"]
        return subprocess.call([str(py_exe), "-m", "pip", *args]) == 0

    def is_installed(pkg_name: str) -> bool:
        """Check if package is installed in the TARGET Python (py_exe), not current Python."""
        try:
            result = subprocess.run(
                [str(py_exe), "-c", f"import importlib.metadata; importlib.metadata.version('{pkg_name}')"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    print("\n--- ?⑦궎吏 ?ㅼ튂 以?---")
    run_pip(["install", "--upgrade", "pip"])

    pkgs = list(BASE_CORE)
    
    # 誘몃뵒???몄쭛 ?⑦궎吏 (Image/Video/Audio 以??섎굹?쇰룄 ?좏깮 ??
    if categories.get("Image") or categories.get("Video") or categories.get("Audio"):
        pkgs += PKG_MEDIA
    
    if categories.get("Document"):
        pkgs += PKG_DOC
    if categories.get("Tools"):
        pkgs += PKG_TOOLS
    if categories.get("3D"):
        pkgs += PKG_3D
    if categories.get("AI"):
        pkgs += PKG_AI_LIGHT
    if categories.get("AI_Heavy"):
        pkgs += PKG_AI_HEAVY

    # Remove duplicates while preserving order
    seen = set()
    final_pkgs = []
    for p in pkgs:
        key = p.split()[0]
        if key in seen:
            continue
        seen.add(key)
        final_pkgs.append(p)

    print(f"?좏깮??移댄뀒怨좊━: {', '.join([k for k,v in categories.items() if v]) or '?놁쓬'}")
    print(f"珥??ㅼ튂 ????⑦궎吏: {len(final_pkgs)}")

    missing_pkgs = []
    for pkg in final_pkgs:
        parts = pkg.split()
        pkg_name = parts[0]
        # Remove version constraints for is_installed check
        clean_name = pkg_name.split('<')[0].split('>')[0].split('=')[0].split('!')[0]
        if is_installed(clean_name):
            print(f"[SKIP] {clean_name} already installed.")
            continue
        missing_pkgs.append(pkg)

    if not missing_pkgs:
        print("紐⑤뱺 ?⑦궎吏媛 ?대? ?ㅼ튂?섏뼱 ?덉뒿?덈떎.")
        return True

    print(f"?ㅼ튂媛 ?꾩슂???⑦궎吏: {len(missing_pkgs)}")
    
    # Group packages by their installation flags to batch them
    # Simple packages vs packages with --index-url, etc.
    standard_batch = []
    special_batches = {} # flag_str -> list of packages

    for pkg in missing_pkgs:
        parts = pkg.split()
        if len(parts) > 1:
            # Has flags (like --index-url)
            flags = " ".join(parts[1:])
            special_batches.setdefault(flags, []).append(parts[0])
        else:
            standard_batch.append(parts[0])

    ok = True

    # 1. Install standard packages in one batch
    if standard_batch:
        print(f"[INSTALL-BATCH] {', '.join(standard_batch)}")
        if not run_pip(["install"] + standard_batch):
            print(f"[寃쎄퀬] ?쒖? ?⑦궎吏 諛곗튂 ?ㅼ튂 ?ㅽ뙣. 媛쒕퀎 ?ㅼ튂 ?쒕룄...")
            # Fallback to individual if batch fails
            for p in standard_batch:
                if not run_pip(["install", p]):
                    print(f"[?ㅻ쪟] {p} ?ㅼ튂 ?ㅽ뙣")
                    ok = False

    # 2. Install special packages in groups
    for flags, pkgs_in_group in special_batches.items():
        flag_parts = flags.split()
        print(f"[INSTALL-SPECIAL] Group with flags '{flags}': {', '.join(pkgs_in_group)}")
        # Combine group: pip install pkg1 pkg2 pkg3 --index-url ...
        if not run_pip(["install"] + pkgs_in_group + flag_parts):
            print(f"[寃쎄퀬] ?뱀닔 ?⑦궎吏 諛곗튂 ?ㅼ튂 ?ㅽ뙣. 媛쒕퀎 ?ㅼ튂 ?쒕룄...")
            for p in pkgs_in_group:
                if not run_pip(["install", p] + flag_parts):
                    print(f"[?ㅻ쪟] {p} ?ㅼ튂 ?ㅽ뙣")
                    ok = False
            
    # Run patches (e.g. basicsr hotfix)
    try:
        patch_path = ROOT_DIR / "src" / "setup"
        if patch_path.exists():
            sys.path.append(str(patch_path))
            import importlib
            try:
                patch_module = importlib.import_module("patch_libs")
                patch_module.run_patches()
            except ImportError:
                print("[INFO] patch_libs.py not found, skipping patches.")
    except Exception as e:
        print(f"[WARN] Failed to run library patches: {e}")

    return ok


def run_gpu_check(py_exe: Path):
    check_script = ROOT_DIR / "src" / "scripts" / "check_gpu_status.py"
    if not check_script.exists():
        return
    print("\nRunning GPU Health Check...")
    try:
        subprocess.call([str(py_exe), str(check_script)])
    except Exception as e:
        print(f"[WARN] GPU check failed: {e}")


def run_model_download(py_exe: Path):
    dl_script = ROOT_DIR / "src" / "setup" / "download_models.py"
    if not dl_script.exists():
        print("[WARN] Model downloader script not found.")
        return False
    print("\nAI 紐⑤뜽 ?ㅼ슫濡쒕뱶 以?(?쒓컙???ㅼ냼 ?뚯슂?????덉뒿?덈떎)...")
    return subprocess.call([str(py_exe), str(dl_script)]) == 0


def load_profile():
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_profile(data: dict):
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def apply_category_defaults_to_overrides(categories: dict[str, bool]):
    """Disable menu items for unchecked categories via user_overrides."""
    try:
        # Collect ids by category
        import glob
        import json as js
        config_dir = ROOT_DIR / "config" / "categories"
        all_ids = []
        for fp in glob.glob(str(config_dir / "*.json")):
            try:
                data = js.loads(Path(fp).read_text(encoding="utf-8"))
                if isinstance(data, list):
                    all_ids.extend([(item.get("category"), item.get("id")) for item in data if item.get("id")])
                elif isinstance(data, dict):
                    # Handle dict-based category with nested 'features'
                    cat = data.get("id", "Unknown") # Or use a default
                    # If it has a 'features' list, use that
                    features = data.get("features", [])
                    if isinstance(features, list):
                        for f in features:
                            fid = f.get("id")
                            if fid:
                                # Use the category from the item or the parent dict
                                f_cat = f.get("category", cat)
                                all_ids.append((f_cat, fid))
                    # Also include the main id if it's a feature itself
                    elif data.get("id"):
                         all_ids.append((data.get("category", cat), data.get("id")))
            except Exception as e:
                print(f"Warning: Failed to parse {fp}: {e}")

        disabled = {cid for cat, cid in all_ids if cat and not categories.get(cat, True)}
        # 蹂듭썝: ?쒖꽦?붾맂 移댄뀒怨좊━????ぉ?ㅼ? hidden?먯꽌 ?쒓굅
        enabled = {cid for cat, cid in all_ids if cat and categories.get(cat, False)}

        overrides = {}
        if USER_OVERRIDES.exists():
            try:
                overrides = json.loads(USER_OVERRIDES.read_text(encoding="utf-8"))
            except Exception:
                overrides = {}

        hidden = set(overrides.get("hidden", []))
        hidden -= enabled  # ?쒖꽦?붾맂 移댄뀒怨좊━ ??ぉ 蹂듭썝
        hidden |= disabled  # 鍮꾪솢?깊솕??移댄뀒怨좊━ ??ぉ ?④?
        overrides["hidden"] = sorted(hidden)
        overrides.setdefault("version", 1)
        overrides.setdefault("overrides", {})
        overrides.setdefault("custom", [])

        USER_OVERRIDES.parent.mkdir(parents=True, exist_ok=True)
        USER_OVERRIDES.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
        print(f"Applied category defaults. Disabled items: {len(disabled)}")
    except Exception as e:
        print(f"[WARN] Failed to apply overrides: {e}")


# Model-to-Feature ID Mapping for Granular Disablement
MODEL_TO_FEATURE = {
    "Whisper": "whisper_subtitle",
    "Upscale": "esrgan_upscale",
    "Rembg": "rmbg_background",
    "Marigold": "marigold_pbr",
    "Demucs": "demucs_stems",
}

def apply_granular_overrides(model_status: dict):
    """Disable specific features based on failed model downloads."""
    try:
        overrides = {}
        if USER_OVERRIDES.exists():
            try:
                overrides = json.loads(USER_OVERRIDES.read_text(encoding="utf-8"))
            except Exception:
                overrides = {}

        hidden = set(overrides.get("hidden", []))
        disabled_features = []
        
        for model_name, success in model_status.items():
            if not success and model_name in MODEL_TO_FEATURE:
                feature_id = MODEL_TO_FEATURE[model_name]
                hidden.add(feature_id)
                disabled_features.append(f"{model_name} -> {feature_id}")
        
        if disabled_features:
            overrides["hidden"] = sorted(hidden)
            overrides.setdefault("version", 1)
            overrides.setdefault("overrides", {})
            overrides.setdefault("custom", [])
            USER_OVERRIDES.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
            print(f"\n[?뺣낫] ?ㅼ쓬 湲곕뒫??紐⑤뜽 ?ㅼ슫濡쒕뱶 ?ㅽ뙣濡?鍮꾪솢?깊솕?섏뿀?듬땲??")
            for item in disabled_features:
                print(f"  - {item}")
    except Exception as e:
        print(f"[WARN] Failed to apply granular overrides: {e}")


def load_tiers() -> dict:
    """install_tiers.json?먯꽌 ?곗뼱 ?ㅼ젙??濡쒕뱶?⑸땲??(userdata ?곗꽑)."""
    # 1. Check userdata first (User Custom Tiers)
    user_tiers = USERDATA_DIR / "install_tiers.json"
    if user_tiers.exists():
        try:
            print(f"[INFO] ?ъ슜???뺤쓽 ?곗뼱 ?ㅼ젙 濡쒕뱶: {user_tiers.name}")
            return json.loads(user_tiers.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] ?ъ슜???곗뼱 ?ㅼ젙 濡쒕뱶 ?ㅽ뙣: {e}")

    # 2. Check defaults
    if TIERS_FILE.exists():
        try:
            return json.loads(TIERS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] ?곗뼱 ?ㅼ젙 濡쒕뱶 ?ㅽ뙣: {e}")
    # 湲곕낯媛?諛섑솚
    return {
        "tiers": {
            "minimal": {"categories": CORE_CATEGORIES},
            "standard": {"categories": CORE_CATEGORIES + ["Image", "Video", "Audio", "Tools", "Sequence"], "ai": "light"},
            "full": {"categories": list(CORE_CATEGORIES) + list(OPTIONAL_CATEGORIES.keys()), "ai": "heavy"}
        },
        "core_categories": CORE_CATEGORIES,
        "category_descriptions": OPTIONAL_CATEGORIES
    }


def choose_install_tier() -> dict[str, bool]:
    """?곗뼱 湲곕컲 ?ㅼ튂 ?좏깮 (install_tiers.json?먯꽌 ?ㅼ젙 濡쒕뱶)"""
    tiers_config = load_tiers()
    tiers = tiers_config.get("tiers", {})
    core_cats = tiers_config.get("core_categories", CORE_CATEGORIES)
    
    # 紐⑤뱺 移댄뀒怨좊━ ?섏쭛
    all_cats = set(core_cats)
    for tier_data in tiers.values():
        all_cats.update(tier_data.get("categories", []))
    
    print("\n" + "="*50)
    print("       ContextUp ?ㅼ튂 ?좏삎 ?좏깮")
    print("="*50)
    
    # ?곗뼱 ?듭뀡 ?쒖떆
    minimal = tiers.get("minimal", {})
    standard = tiers.get("standard", {})
    full = tiers.get("full", {})
    
    print(f"\n[1] {minimal.get('name', 'Minimal install')}")
    print(f"    - {minimal.get('description', 'Core features only')}")
    
    print(f"\n[2] {standard.get('name', 'Standard install')} (Recommended)")
    print(f"    - {standard.get('description', 'General features + media')}")
    
    print(f"\n[3] {full.get('name', 'Full install')}")
    print(f"    - {full.get('description', 'All features + AI')}")
    
    
    choice = input("\n?ㅼ튂 ?좏삎???좏깮?섏꽭??[1-3] (湲곕낯=2): ").strip() or "2"
    if choice not in ("1", "2", "3"):
        choice = "2"
    
    # 移댄뀒怨좊━ 珥덇린??(紐⑤뱺 移댄뀒怨좊━ False)
    categories = {cat: False for cat in all_cats}
    categories["AI"] = False
    categories["AI_Heavy"] = False
    
    def apply_tier(tier_key: str):
        tier_data = tiers.get(tier_key, {})
        for cat in tier_data.get("categories", []):
            categories[cat] = True
        ai_level = tier_data.get("ai", "")
        if ai_level in ("light", "heavy"):
            categories["AI"] = True
        if ai_level == "heavy":
            categories["AI_Heavy"] = True
    
    if choice == "1":
        print("\n>>> Selected: Minimal install")
        apply_tier("minimal")
        return categories
    
    elif choice == "2":
        print("\n>>> Selected: Standard install")
        apply_tier("standard")
        return categories
    
    elif choice == "3":
        print("\n>>> Selected: Full install")
        apply_tier("full")
        return categories
    


def print_summary(categories: dict, tools_res: dict, models_ok: bool, pkg_ok: bool, models_attempted: bool):
    print("\n==========================================")
    print("           ?ㅼ튂 寃곌낵 ?붿빟")
    print("==========================================")
    print(f"?뚯씠???섍꼍  : ?댁옣 ?뚯씠??(Ready)")
    print(f"?⑦궎吏 ?ㅼ튂  : {'?깃났' if pkg_ok else '?쇰? ?ㅽ뙣'}")
    
    print("\n[移댄뀒怨좊━]")
    for cat, enabled in categories.items():
        if enabled:
            print(f"  - {cat}")
            
    print("\n[?몃? ?꾧뎄]")
    if tools_res:
        for tool, success in tools_res.items():
            status = "OK" if success else "FAIL"
            print(f"  - {tool}: {status}")
    else:
        print("  (?ㅼ튂 嫄대꼫?)")

    if categories.get("AI_Heavy"):
        print("\n[AI 紐⑤뜽]")
        if not models_attempted:
            print("  - ?곹깭: 誘몄떎??(?ㅼ튂 ???ㅼ슫濡쒕뱶 ?앸왂)")
        elif models_ok:
            print(f"  - ?곹깭: 以鍮꾨맖 (All Models Ready)")
        else:
            print(f"  - ?곹깭: [二쇱쓽] ?쇰? 紐⑤뜽 ?ㅼ슫濡쒕뱶 ?ㅽ뙣")
            print(f"          (?섏쨷??'src/setup/download_models.py'瑜?吏곸젒 ?ㅽ뻾?섏뿬 ?ъ떆?꾪븯?몄슂)")

    print("==========================================\n")


def main():
    print("=== ContextUp ?ㅼ튂 愿由ъ옄 (?댁옣 ?뚯씠???꾩슜) ===\n")
    safe_test = os.environ.get(SAFE_TEST_ENV) == "1"
    if safe_test:
        print("[INFO] SAFE TEST mode enabled. Registry and manager launch will be skipped.")
    
    # 2025-12-23: Migrate existing user data from config/ to userdata/
    try:
        from core.paths import migrate_legacy_userdata
        migrate_legacy_userdata()
    except Exception as e:
        print(f"[寃쎄퀬] ?ъ슜???곗씠??留덉씠洹몃젅?댁뀡 ?ㅽ뙣: {e}")
        try:
            migrate_userdata()
        except Exception as inner_e:
            print(f"[寃쎄퀬] ?ъ슜???곗씠??留덉씠洹몃젅?댁뀡 ?ъ떆???ㅽ뙣: {inner_e}")
    
    profile = load_profile()
    
    # Force Embedded Python setup
    chosen_python = setup_embedded_python(force_reinstall=False)

    if not chosen_python or not _python_ok(chosen_python):
        print("[?ㅻ쪟] ?좏슚???뚯씠???섍꼍??援ъ꽦?????놁뒿?덈떎 (tkinter ?꾩닔).")
        return

    categories = choose_install_tier()
    # External tools are not auto-installed (manual setup for advanced users).
    tools_results = {}

    pkg_ok = install_packages(chosen_python, categories)

    download_models = categories.get("AI_Heavy") and pkg_ok
    if safe_test and download_models:
        print("[INFO] SAFE TEST mode enabled. Skipping model downloads and GPU checks.")
        download_models = False
    models_ok = True
    model_status = {}
    if download_models:
        models_ok = run_model_download(chosen_python)
        # Read model status from JSON if available
        model_status_file = ROOT_DIR / "config" / "model_status.json"
        if model_status_file.exists():
            try:
                model_status = json.loads(model_status_file.read_text(encoding="utf-8"))
            except Exception:
                model_status = {}
        if not models_ok:
            print("\n[二쇱쓽] ?쇰? AI 紐⑤뜽 ?ㅼ슫濡쒕뱶 ?ㅽ뙣. 愿??湲곕뒫??鍮꾪솢?깊솕?⑸땲??")
            # Apply granular disablement instead of entire category
            apply_granular_overrides(model_status)

    if categories.get("AI_Heavy") and pkg_ok and not safe_test:
        run_gpu_check(chosen_python)

    # Persist profile
    profile = {
        "python_path": str(chosen_python),
        "python_version": subprocess.check_output([str(chosen_python), "-c", "import sys;print(sys.version.split()[0])"], text=True).strip(),
        "categories": categories,
        "models_pre_downloaded": bool(download_models and models_ok),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    save_profile(profile)
    apply_category_defaults_to_overrides(categories)

    # Print Summary
    print_summary(categories, tools_results, models_ok, pkg_ok, bool(download_models))

    # Log upload on failure
    if not pkg_ok or not models_ok:
        print("\n[寃쎄퀬] ?ㅼ튂 以??쇰? ?ㅻ쪟媛 諛쒖깮?덉뒿?덈떎.")
        log_path = ROOT_DIR / "install_log.txt"
        if prompt_yn("?ㅻ쪟 濡쒓렇瑜?媛쒕컻?먯뿉寃??꾩넚?섏떆寃좎뒿?덇퉴?", False):
            try:
                # Save log file (placeholder for actual log capture)
                log_content = f"Install Log - {datetime.now().isoformat()}\n"
                log_content += f"Package OK: {pkg_ok}\n"
                log_content += f"Models OK: {models_ok}\n"
                log_content += f"Model Status: {json.dumps(model_status, indent=2)}\n"
                log_content += f"Categories: {json.dumps(categories, indent=2)}\n"
                log_path.write_text(log_content, encoding="utf-8")
                print(f"濡쒓렇媛 ??λ릺?덉뒿?덈떎: {log_path}")
                print("媛쒕컻?먯뿉寃??섎룞?쇰줈 ?꾨떖?섍굅??GitHub Issue濡??쒖텧??二쇱꽭??")
                print("  https://github.com/simiroa/CONTEXTUP/issues")
            except Exception as e:
                print(f"濡쒓렇 ????ㅽ뙣: {e}")
    else:
        print("[?깃났] ?ㅼ튂 ?④퀎媛 ?꾨즺?섏뿀?듬땲??")
        
    print("\n" + "!"*50)
    print(" [以묒슂 怨듭?] ?몃? ?꾧뎄 ?ㅼ튂 ?꾩슂")
    print("!"*50)
    print(" ???ㅼ튂 ?꾨줈洹몃옩? ContextUp 湲곕낯 ?꾨젅?꾩썙?ъ? ?꾩닔 ?꾧뎄瑜??ㅼ튂?⑸땲??")
    print(" ?ㅼ쓬 ?꾧뎄?ㅼ? ?쇱씠?쇱뒪 諛??⑸웾 臾몄젣濡??ъ슜?먭? 吏곸젒 ?ㅼ튂?댁빞 ?⑸땲??")
    print("  - ComfyUI (Generative AI)")
    print("  - Ollama (Local LLM)")
    print("  - Rhino/Blender (3D Tools)")
    print("\n ?ㅼ튂 ??'?ㅼ젙 -> ?몃? ?꾧뎄 寃쎈줈'?먯꽌 媛??ㅽ뻾 ?뚯씪(.exe) ?꾩튂瑜?吏?뺥빐 二쇱꽭??")
    print("!"*50 + "\n")
    
    if not safe_test:
        # 2025-12-21: Auto-register context menu
        print("\n而⑦뀓?ㅽ듃 硫붾돱瑜??깅줉?⑸땲??..")
        try:
            reg_script = ROOT_DIR / "re_register_menu.py"
            subprocess.call([str(chosen_python), str(reg_script)])
        except Exception as e:
            print(f"[寃쎄퀬] 硫붾돱 ?깅줉 ?ㅽ뙣: {e}")

        print("\nContextUp 留ㅻ땲?瑜??ㅽ뻾?⑸땲??..")
        # GUI 留ㅻ땲???src/manager/main.py???덉쓬 (manage.py??CLI ?꾧뎄)
        manager_script = ROOT_DIR / "src" / "manager" / "main.py"
        if manager_script.exists():
            try:
                # Use the verified python executable to launch manager GUI
                # DETACHED_PROCESS to allow installer to close
                creationflags = 0x00000008  # DETACHED_PROCESS on Windows
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW
                
                # Use Popen to launch and proceed
                subprocess.Popen(
                    [str(chosen_python), str(manager_script)], 
                    cwd=str(ROOT_DIR),
                    creationflags=creationflags
                )
                print("留ㅻ땲?媛 ?ㅽ뻾?섏뿀?듬땲??")
            except Exception as e:
                print(f"留ㅻ땲? ?ㅽ뻾 ?ㅽ뙣: {e}")
        else:
            print(f"留ㅻ땲? ?ㅽ겕由쏀듃瑜?李얠쓣 ???놁뒿?덈떎: {manager_script}")

        input("\n醫낅즺?섎젮硫??뷀꽣 ?ㅻ? ?꾨Ⅴ?몄슂...")


if __name__ == "__main__":
    main()
