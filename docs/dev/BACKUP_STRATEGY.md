# ContextUp Backup Strategy

To ensure code safety and reproducibility, please follow this backup strategy.

## 1. What to Backup (Essential)
Regularly backup these core directories. They contain all the source code and configurations.

*   `src/` - All Python source code and scripts.
*   `config/` - Menu configurations (`.json`) and specific tool presets.
*   `assets/` - Icons and resources.
*   `tests/` - Test scripts.
*   `docs/` - Documentation.
*   `install/` - Installation scripts.
*   `*.md` - All markdown files in the root (`README.md`, `DEVELOPMENT.md`, etc.).
*   `run_*.bat` - Launcher scripts.

## 2. What to Exclude (Heavy/Generated items)
Do **NOT** backup these folders as they are large and can be re-downloaded or re-generated.

*   `.gemini/` - AI Cache and Artifacts.
*   `tools/` - **Embedded Python Environment**. This is very heavy (~3-5GB). It can be re-installed via `install/install_python.bat`.
*   `.cache/` - Hugging Face model cache (usually in User Home, but worth noting).
*   `__pycache__/` - Compiled Python files.
*   `*.log` - Debug logs (`debug.log`).

## 3. Recommended Backup Method (Zip/7z)
Create a compressed archive of the project root, excluding the heavy folders.

**Command Line (PowerShell):**
```powershell
Compress-Archive -Path "config", "src", "assets", "docs", "install", "*.md", "*.bat" -DestinationPath "ContextUp_Backup_2025-12-09.zip"
```

**Git Strategy:**
Ensure `.gitignore` includes:
```
tools/
.gemini/
__pycache__/
*.log
```

## 4. Model Weights
Marigold models are cached in `~/.cache/huggingface/hub`.
If offline usage is required, consider backing up this specific cache folder separately, but do not include it in the source code backup.
