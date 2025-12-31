import sys
import os
import shutil
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Add src to path to import utils
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
sys.path.append(str(SRC_DIR))
sys.path.append(str(SRC_DIR.parent / "libs")) # Legacy support

try:
    from utils import paths
except ImportError:
    print("Error: Could not import utils.paths. Ensure running from project context.")
    sys.exit(1)

def migrate_legacy_caches():
    """Move existing models from global cache to localized cache if found."""
    print("\n=== checking for Legacy Models to Migrate ===")
    user_home = Path(os.path.expanduser("~"))
    
    # 1. Rembg (u2net)
    legacy_u2net = user_home / ".u2net"
    target_u2net = paths.REMBG_DIR
    
    if legacy_u2net.exists():
        if not target_u2net.exists() or not any(target_u2net.iterdir()):
            print(f"Migrating Rembg models from {legacy_u2net} to {target_u2net}...")
            try:
                target_u2net.mkdir(parents=True, exist_ok=True)
                for item in legacy_u2net.iterdir():
                    if item.is_file():
                        shutil.copy2(item, target_u2net / item.name)
                print("Rembg migration successful.")
            except Exception as e:
                print(f"Rembg migration failed: {e}")
        else:
            print(f"Target Rembg folder not empty, skipping migration.")
    
    # 2. Legacy resources in src/resources -> resources
    legacy_resources = paths.PROJECT_ROOT / "src" / "resources"
    legacy_ai_models = legacy_resources / "ai_models"
    if legacy_ai_models.exists():
        try:
            if not paths.AI_MODELS_DIR.exists() or not any(paths.AI_MODELS_DIR.iterdir()):
                print(f"Migrating legacy AI models from {legacy_ai_models} to {paths.AI_MODELS_DIR}...")
                paths.AI_MODELS_DIR.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(legacy_ai_models), str(paths.AI_MODELS_DIR))
                print("Legacy AI models migration successful.")
            else:
                print("Target AI models folder not empty, skipping legacy migration.")
        except Exception as e:
            print(f"Legacy AI models migration failed: {e}")

    legacy_bin = legacy_resources / "bin"
    if legacy_bin.exists():
        try:
            if not paths.BIN_DIR.exists() or not any(paths.BIN_DIR.iterdir()):
                print(f"Migrating legacy binaries from {legacy_bin} to {paths.BIN_DIR}...")
                paths.BIN_DIR.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(legacy_bin), str(paths.BIN_DIR))
                print("Legacy binaries migration successful.")
            else:
                print("Target bin folder not empty, skipping legacy migration.")
        except Exception as e:
            print(f"Legacy binaries migration failed: {e}")

    # 3. HF Models (Complex, risk of corruption, so verified download is preferred)
    # But we can try to copy if user insists on "moving".
    # However, diffusers/HF cache structure is hash-based. Simple move might fail validation.
    # We will skip HF migration and rely on re-download which checks hashes anyway.
    # We will skip HF migration and rely on re-download which checks hashes anyway.
    return

def download_marigold():
    print("\n=== Checking Marigold Models (Depth/Normal/Appearance) ===")
    print(f"Target Dir: {paths.MARIGOLD_DIR}")
    try:
        from diffusers import MarigoldDepthPipeline, MarigoldNormalsPipeline, MarigoldIntrinsicsPipeline
        import torch
        
        # Ensure dir exists
        paths.MARIGOLD_DIR.mkdir(parents=True, exist_ok=True)
        
        print("Checking Depth Model...")
        MarigoldDepthPipeline.from_pretrained(
            "prs-eth/marigold-depth-v1-1", 
            cache_dir=paths.MARIGOLD_DIR
        )
        
        print("Checking Normal Model...")
        MarigoldNormalsPipeline.from_pretrained(
            "prs-eth/marigold-normals-v1-1", 
            cache_dir=paths.MARIGOLD_DIR
        )
        
        print("Checking Appearance Model (Albedo/Roughness)...")
        MarigoldIntrinsicsPipeline.from_pretrained(
            "prs-eth/marigold-iid-appearance-v1-1",
            cache_dir=paths.MARIGOLD_DIR
        )
        
    except ImportError:
        print("Marigold Download Failed: 'diffusers' library not found. Ensure 'AI_Heavy' was selected during install.")
        return False
    except Exception as e:
        print(f"Marigold Download Failed: {e}")
        return False

def download_rembg():
    print("\n=== Checking Rembg Models ===")
    
    # Set Env Var for Rembg
    os.environ["U2NET_HOME"] = str(paths.REMBG_DIR)
    paths.REMBG_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        from rembg import new_session
        print(f"Target Dir: {paths.REMBG_DIR}")
        new_session("u2net")
        new_session("u2net")
        print("Rembg Models Verified.")
        return True
    except Exception as e:
        print(f"Rembg Download Failed: {e}")
        return False

def download_birefnet():
    print("\n=== Checking BiRefNet (General Use) ===")
    try:
        from transformers import AutoModelForImageSegmentation
        
        print("Verifying 'ZhengPeng7/BiRefNet'...")
        # Check download/cache
        AutoModelForImageSegmentation.from_pretrained("ZhengPeng7/BiRefNet", trust_remote_code=True)
        print("BiRefNet Verified.")
        return True
    except Exception as e:
        print(f"BiRefNet Download Failed: {e}")
        return False

def download_demucs():
    print("\n=== Checking Demucs Models (Audio Separation) ===")
    try:
        # Set TORCH_HOME for localized cache
        os.environ["TORCH_HOME"] = str(paths.DEMUCS_DIR)
        paths.DEMUCS_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"Target Dir (TORCH_HOME): {paths.DEMUCS_DIR}")
        
        from demucs.pretrained import get_model
        print("Downloading Demucs 'htdemucs' model...")
        get_model('htdemucs')
        get_model('htdemucs')
        print("Demucs Models Verified.")
        return True
    except Exception as e:
        print(f"Demucs Download Failed: {e}")
        return False

def download_whisper():
    print("\n=== Checking Whisper Models (Speech-to-Text) ===")
    try:
        from faster_whisper import WhisperModel
        
        TARGET_DIR = paths.WHISPER_DIR
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Target Dir: {TARGET_DIR}")

        print("Downloading/Verifying 'small' model...")
        WhisperModel("small", device="cpu", compute_type="int8", download_root=str(TARGET_DIR))
        
        print("Downloading/Verifying 'medium' model...")
        WhisperModel("medium", device="cpu", compute_type="int8", download_root=str(TARGET_DIR))
        
        print("Whisper Models Ready.")
        return True
    except Exception as e:
        print(f"Whisper Download Failed: {e}")
        return False

def download_rmbg20():
    print("\n=== Checking RMBG-2.0 (BriaAI) ===")
    try:
        from transformers import AutoModelForImageSegmentation
        from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError, LocalTokenNotFoundError
        
        print("Verifying 'briaai/RMBG-2.0' (Gated Model)...")
        # RMBG-2.0 is gated. It requires HF_TOKEN or huggingface-cli login.
        try:
            # Try loading. If not logged in and not cached, this will fail.
            AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-2.0", trust_remote_code=True)
            print("RMBG-2.0 Verified.")
            return True
        except (GatedRepoError, LocalTokenNotFoundError, OSError) as e:
            # Check if it's an auth issue
            error_msg = str(e).lower()
            if "401" in error_msg or "403" in error_msg or "gated" in error_msg or "token" in error_msg:
                print("\n[Auth Required] RMBG-2.0 is a gated model.")
                print("1. Create a Hugging Face account and agree to the license at: https://huggingface.co/briaai/RMBG-2.0")
                print("2. Create an Access Token: https://huggingface.co/settings/tokens")
                print("3. Run: `huggingface-cli login` in your terminal and paste the token.")
                print("   Or set environment variable: set HF_TOKEN=<your_token>")
                print(f"Details: {e}")
                return False
            else:
                raise e
            
    except Exception as e:
        print(f"RMBG-2.0 Download Failed: {e}")
        return False

def download_upscale():
    print("\n=== Checking Upscale Models (RealESRGAN/GFPGAN) ===")
    try:
        from features.ai.standalone.upscale import ensure_model
        ensure_model('RealESRGAN_x4plus')
        
        print("Checking GFPGAN...")
        from gfpgan import GFPGANer
        GFPGANer(model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth', 
                upscale=1, arch='clean', channel_multiplier=2)
        print("GFPGAN Verified.")
        return True
    except Exception as e:
        print(f"Upscale Download Failed: {e}")
        return False

    print("\n=== Checking RIFE Models (Video Interpolation) ===")
    bin_path = paths.BIN_DIR / "rife"
    exe_path = bin_path / "rife-ncnn-vulkan.exe"
    
    if exe_path.exists():
        print(f"RIFE Binary found: {exe_path}")
        model_path = bin_path / "rife-v4.6"
        if model_path.exists():
             print("RIFE v4.6 Model found.")
             return True
        else:
             print("WARNING: RIFE v4.6 model folder missing in bin/rife/")
             return False
    else:
        print(f"WARNING: RIFE binary not found at {exe_path}")
        return False

def main():
    print("ContextUp Model Downloader (Standardized Path)")
    print(f"Resources Dir: {paths.RESOURCES_DIR}")
    
    migrate_legacy_caches()
    
    results = {
        "Rembg": download_rembg(),
        "BiRefNet": download_birefnet(),
        "Marigold": download_marigold(),
        "Upscale": download_upscale(),
        "Whisper": download_whisper(),
        "Demucs": download_demucs(),
        "RMBG-2.0": download_rmbg20(),
    }
    
    print("\n=== Model Download Summary ===")
    failed = []
    for name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {name:<10}: {status}")
        if not success:
            failed.append(name)
    
    # Save status to JSON for install.py to read
    import json
    status_file = paths.PROJECT_ROOT / "config" / "model_status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[INFO] Model status saved to: {status_file}")
            
    if failed:
        print(f"\n[WARNING] The following models failed to download: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAll model checks completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
