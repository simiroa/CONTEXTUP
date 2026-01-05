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

# Force UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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
# 카테고리 분류
# ============================================================

# 항상 설치되는 기본 카테고리 (사용자가 선택하지 않아도 자동 포함)
CORE_CATEGORIES = ["System", "Rename", "Clipboard", "Document"]

# 사용자가 선택 가능한 옵션 카테고리
OPTIONAL_CATEGORIES = {
    "Image": "이미지 편집 (형식 변환, 리사이즈, 워터마크 등)",
    "Video": "비디오 처리 (변환, 자르기, GIF 생성) - FFmpeg 필요",
    "Audio": "오디오 편집 (변환, 볼륨 조절) - FFmpeg 필요",
    "3D": "3D 도구 (모델 변환, 리메쉬)",
    "Tools": "유틸리티 (번역기 등)",
    "Sequence": "시퀀스 도구 (이미지 시퀀스 관리, 비디오 변환)",
    "ComfyUI": "ComfyUI 통합 (생성형 AI) - ComfyUI 설치 필요",
}

# ============================================================
# 패키지 그룹
# ============================================================

# 기본 핵심 패키지 (항상 설치)
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
    "holidays",
]

# 미디어 편집용 패키지 (Image/Video/Audio 중 하나라도 선택 시)
PKG_MEDIA = [
    "ffmpeg-python",
    "imageio",
    "OpenEXR",
    "scipy",
    "rawpy",
    "pillow-heif",
    "opencv-python",
    "noise",
]

# 문서 처리 패키지
PKG_DOC = ["pypdf", "PyPDF2", "pdf2image", "pdf2docx", "pymupdf4llm", "svglib", "reportlab"]

# 유틸리티 패키지
PKG_TOOLS = ["deep-translator", "yt-dlp"]

# 3D 패키지
PKG_3D = ["pymeshlab"]


# AI Light: API 기반 (가벼움, ~100MB)
PKG_AI_LIGHT = [
    "google-generativeai",
    "google-genai",
    "ollama",
]

# AI Heavy: 로컬 모델 (무거움, ~8-10GB)
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
    "hf_xet",  # Suppress Xet Storage warnings and improve DL speed
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
                print(f"[WARN] 마이그레이션 실패 {old_path.name}: {e}")
    
    if migrated:
        print(f"[INFO] 사용자 데이터 마이그레이션 완료: {', '.join(migrated)}")
    
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

    print("\n--- 패키지 설치 중 ---")
    run_pip(["install", "--upgrade", "pip"])

    pkgs = list(BASE_CORE)
    
    # 미디어 편집 패키지 (Image/Video/Audio 중 하나라도 선택 시)
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

    print(f"선택된 카테고리: {', '.join([k for k,v in categories.items() if v]) or '없음'}")
    print(f"총 설치 대상 패키지: {len(final_pkgs)}")

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
        print("모든 패키지가 이미 설치되어 있습니다.")
        return True

    print(f"설치가 필요한 패키지: {len(missing_pkgs)}")
    
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
            print(f"[경고] 표준 패키지 배치 설치 실패. 개별 설치 시도...")
            # Fallback to individual if batch fails
            for p in standard_batch:
                if not run_pip(["install", p]):
                    print(f"[오류] {p} 설치 실패")
                    ok = False

    # 2. Install special packages in groups
    for flags, pkgs_in_group in special_batches.items():
        flag_parts = flags.split()
        print(f"[INSTALL-SPECIAL] Group with flags '{flags}': {', '.join(pkgs_in_group)}")
        # Combine group: pip install pkg1 pkg2 pkg3 --index-url ...
        if not run_pip(["install"] + pkgs_in_group + flag_parts):
            print(f"[경고] 특수 패키지 배치 설치 실패. 개별 설치 시도...")
            for p in pkgs_in_group:
                if not run_pip(["install", p] + flag_parts):
                    print(f"[오류] {p} 설치 실패")
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
    print("\nAI 모델 다운로드 중 (시간이 다소 소요될 수 있습니다)...")
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
        # 복원: 활성화된 카테고리 항목들은 hidden에서 제거
        enabled = {cid for cat, cid in all_ids if cat and categories.get(cat, False)}

        overrides = {}
        if USER_OVERRIDES.exists():
            try:
                overrides = json.loads(USER_OVERRIDES.read_text(encoding="utf-8"))
            except Exception:
                overrides = {}

        hidden = set(overrides.get("hidden", []))
        hidden -= enabled  # 활성화된 카테고리 항목 복원
        hidden |= disabled  # 비활성화된 카테고리 항목 추가
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
            overrides.setdefault("custom", [])
            USER_OVERRIDES.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
            print(f"\n[정보] 다음 기능이 모델 다운로드 실패로 비활성화되었습니다:")
            for item in disabled_features:
                print(f"  - {item}")
    except Exception as e:
        print(f"[WARN] Failed to apply granular overrides: {e}")


def load_tiers() -> dict:
    """install_tiers.json에서 티어 설정을 로드합니다 (userdata 우선)."""
    # 1. Check userdata first (User Custom Tiers)
    user_tiers = USERDATA_DIR / "install_tiers.json"
    if user_tiers.exists():
        try:
            print(f"[INFO] 사용자 정의 티어 설정 로드: {user_tiers.name}")
            return json.loads(user_tiers.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] 사용자 티어 설정 로드 실패: {e}")

    # 2. Check defaults
    if TIERS_FILE.exists():
        try:
            return json.loads(TIERS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] 티어 설정 로드 실패: {e}")
    # 기본값 반환
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
    """티어 기반 설치 선택 (install_tiers.json에서 설정 로드)"""
    tiers_config = load_tiers()
    tiers = tiers_config.get("tiers", {})
    core_cats = tiers_config.get("core_categories", CORE_CATEGORIES)
    
    # 모든 카테고리 수집
    all_cats = set(core_cats)
    for tier_data in tiers.values():
        all_cats.update(tier_data.get("categories", []))
    
    print("\n" + "="*50)
    print("       ContextUp 설치 유형 선택")
    print("="*50)
    
    # 티어 옵션 표시
    minimal = tiers.get("minimal", {})
    standard = tiers.get("standard", {})
    full = tiers.get("full", {})
    
    print(f"\n[1] {minimal.get('name', 'Minimal install')}")
    print(f"    - {minimal.get('description', 'Core features only')}")
    
    print(f"\n[2] {standard.get('name', 'Standard install')} (Recommended)")
    print(f"    - {standard.get('description', 'General features + media')}")
    
    print(f"\n[3] {full.get('name', 'Full install')}")
    print(f"    - {full.get('description', 'All features + AI')}")
    
    
    choice = input("\n설치 유형을 선택하세요 [1-3] (기본=2): ").strip() or "2"
    if choice not in ("1", "2", "3"):
        choice = "2"
    
    # 카테고리 초기화 (모든 카테고리 False)
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
    print("           설치 결과 요약")
    print("==========================================")
    print(f"파이썬 환경  : 내장 파이썬 (Ready)")
    print(f"패키지 설치  : {'성공' if pkg_ok else '일부 실패'}")
    
    print("\n[카테고리]")
    for cat, enabled in categories.items():
        if enabled:
            print(f"  - {cat}")
            
    print("\n[외부 도구]")
    if tools_res:
        for tool, success in tools_res.items():
            status = "OK" if success else "FAIL"
            print(f"  - {tool}: {status}")
    else:
        print("  (설치 건너뜀)")

    if categories.get("AI_Heavy"):
        print("\n[AI 모델]")
        if not models_attempted:
            print("  - 상태: 미설치 (설치 중 다운로드 생략)")
        elif models_ok:
            print(f"  - 상태: 준비됨 (All Models Ready)")
        else:
            print(f"  - 상태: [주의] 일부 모델 다운로드 실패")
            print(f"          (나중에 'src/setup/download_models.py'를 직접 실행하여 재시도하세요)")

    print("==========================================\n")


def main():
    print("=== ContextUp 설치 관리자 (내장 파이썬 전용) ===\n")
    safe_test = os.environ.get(SAFE_TEST_ENV) == "1"
    if safe_test:
        print("[INFO] SAFE TEST mode enabled. Registry and manager launch will be skipped.")
    
    # 2025-12-23: Migrate existing user data from config/ to userdata/
    try:
        from core.paths import migrate_legacy_userdata
        migrate_legacy_userdata()
    except Exception as e:
        print(f"[경고] 사용자 데이터 마이그레이션 실패: {e}")
        try:
            migrate_userdata()
        except Exception as inner_e:
            print(f"[경고] 사용자 데이터 마이그레이션 재시도 실패: {inner_e}")
    
    profile = load_profile()
    
    # Force Embedded Python setup
    chosen_python = setup_embedded_python(force_reinstall=False)

    if not chosen_python or not _python_ok(chosen_python):
        print("[오류] 유효한 파이썬 환경을 구성할 수 없습니다 (tkinter 필수).")
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
            print("\n[주의] 일부 AI 모델 다운로드 실패. 관련 기능이 비활성화됩니다.")
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

    # Register context menu BEFORE error logging (should proceed even if some models failed)
    if not safe_test and pkg_ok:
        print("\n컨텍스트 메뉴를 등록합니다...")
        try:
            reg_script = ROOT_DIR / "re_register_menu.py"
            result = subprocess.call([str(chosen_python), str(reg_script)])
            if result == 0:
                print("[성공] 컨텍스트 메뉴 등록 완료.")
            else:
                print(f"[경고] 메뉴 등록 스크립트가 오류 코드 {result}를 반환했습니다.")
        except Exception as e:
            print(f"[경고] 메뉴 등록 실패: {e}")

    # Log upload on failure (model failures are low severity, don't block installation)
    if not pkg_ok:
        print("\n[경고] 설치 중 일부 오류가 발생했습니다.")
        log_path = ROOT_DIR / "install_log.txt"
        if prompt_yn("오류 로그를 개발자에게 전송하시겠습니까?", False):
            try:
                # Save log file (placeholder for actual log capture)
                log_content = f"Install Log - {datetime.now().isoformat()}\n"
                log_content += f"Package OK: {pkg_ok}\n"
                log_content += f"Models OK: {models_ok}\n"
                log_content += f"Model Status: {json.dumps(model_status, indent=2)}\n"
                log_content += f"Categories: {json.dumps(categories, indent=2)}\n"
                log_path.write_text(log_content, encoding="utf-8")
                print(f"로그가 저장되었습니다: {log_path}")
                print("개발자에게 수동으로 전달하거나 GitHub Issue로 제출해 주세요.")
                print("  https://github.com/simiroa/CONTEXTUP/issues")
            except Exception as e:
                print(f"로그 저장 실패: {e}")
    else:
        print("[성공] 설치 단계가 완료되었습니다.")
        
    print("\n" + "!"*50)
    print(" [중요 공지] 외부 도구 설치 필요")
    print("!"*50)
    print(" 본 설치 프로그램은 ContextUp 기본 프레임워크와 필수 도구를 설치합니다.")
    print(" 다음 도구들은 라이선스 및 용량 문제로 사용자가 직접 설치해야 합니다.")
    print("  - ComfyUI (Generative AI)")
    print("  - Ollama (Local LLM)")
    print("  - Rhino/Blender (3D Tools)")
    print("\n 설치 후 '설정 -> 외부 도구 경로'에서 각 실행 파일(.exe) 위치를 지정해 주세요.")
    print("!"*50 + "\n")
    
    if not safe_test:

        print("\nContextUp 매니저를 실행합니다...")
        # GUI 매니저는 src/manager/main.py에 있음 (manage.py는 CLI 도구)
        manager_script = ROOT_DIR / "src" / "manager" / "main.py"
        if manager_script.exists():
            try:
                # Use the verified python executable to launch manager GUI
                # DETACHED_PROCESS to allow installer to close
                creationflags = 0x00000008  # DETACHED_PROCESS on Windows
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW
                
                # Use Popen to launch and proceed
                # Note: Using direct script execution instead of -m flag
                # because -m requires the package to be importable BEFORE the script runs,
                # but we need main.py to set up sys.path first.
                
                subprocess.Popen(
                    [str(chosen_python), str(manager_script)], 
                    cwd=str(ROOT_DIR),
                    # Show console for debugging on first launch
                    creationflags=0 
                )
                print("매니저 실행 요청을 보냈습니다. (오류가 발생하면 새 창에 표시됩니다.)")
            except Exception as e:
                print(f"매니저 실행 실패: {e}")
        else:
            print(f"매니저 스크립트를 찾을 수 없습니다: {manager_script}")

        input("\n종료하려면 엔터 키를 누르세요...")


if __name__ == "__main__":
    main()
