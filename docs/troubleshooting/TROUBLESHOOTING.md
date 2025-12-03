# Troubleshooting Guide

This guide covers common issues related to the ContextUp tools, including GUI problems, system errors, and AI/HuggingFace configuration.

---

## 1. General GUI & System Issues

### 1.1. GUI Not Appearing (Tkinter Issues)
**Symptoms:**
- Script runs but no window appears.
- Error logs show `ImportError: DLL load failed` or `_tkinter` module not found.

**Cause:**
- Embedded Python environment missing `tcl/tk` libraries or DLLs.
- `zlib1.dll` missing from `tools/python` directory.

**Solution:**
- Ensure `tcl` and `tk` folders are present in `tools/python/Lib`.
- Ensure `tcl86t.dll`, `tk86t.dll`, and `zlib1.dll` are in `tools/python`.
- Use `os.add_dll_directory` in the script.

### 1.2. "AttributeError: 'X' object has no attribute 'Y'"
**Symptoms:**
- Script crashes immediately on startup.
- Error log points to a missing widget (e.g., `self.status_label`) or method.

**Cause:**
- **Incomplete Code Edits**: When using AI tools to edit code, replacing a method with a placeholder (e.g., `# ... same ...`) effectively deletes the method body if not handled carefully.
- **Missing Initialization**: Calling a method (like `create_widgets`) that was accidentally deleted or empty.

**Solution:**
- **Always verify file content** after an edit.
- Restore the missing method body.

### 1.3. Translator "Waiting..." Forever
**Symptoms:**
- Status stays on "Loading..." or "Translating..." indefinitely.

**Cause:**
- **Deadlock**: Using `intra_threads > 1` in `ctranslate2` on certain environments can cause the process to hang.
- **Blocking Main Thread**: Loading large models on the main UI thread freezes the window.

**Solution:**
- Set `intra_threads=1` for `ctranslate2.Translator`.
- Move model loading and inference to a background thread (`threading.Thread`).

---

## 2. AI & HuggingFace Issues

### 2.1. HuggingFace Authentication (RMBG-2.0 / BiRefNet)
**Symptoms:**
- "401 Client Error" when downloading models.
- "Repository Not Found" for gated models.

**Solution:**

#### Step 1: Create Account & Token
1. Join [HuggingFace](https://huggingface.co/join).
2. Go to [Settings > Tokens](https://huggingface.co/settings/tokens).
3. Create a **Read** token.

#### Step 2: Request Access
1. Visit [RMBG-2.0](https://huggingface.co/briaai/RMBG-2.0) and accept terms.
2. Visit [BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet) and accept terms.

#### Step 3: Configure Token
Run in your Conda environment:
```bash
pip install huggingface-hub
python -c "from huggingface_hub import login; login('YOUR_TOKEN_HERE')"
```
Or set environment variable:
```powershell
$env:HF_TOKEN = "YOUR_TOKEN_HERE"
```

### 2.2. Conda Environment Not Found
**Symptoms:**
- Error: "Conda environment not set up" or "env_info.txt not found".

**Cause:**
- `ai_runner.py` cannot locate the `env_info.txt` configuration file.

**Solution:**
1. **Auto-fix**: Run `python tools/fix_ai_env.py`.
2. **Manual Fix**: Check/Create `src/scripts/ai_standalone/env_info.txt` with:
   ```ini
   CONDA_ENV_PATH=C:\Users\HG\miniconda3\envs\ai_tools
   PYTHON_EXE=C:\Users\HG\miniconda3\envs\ai_tools\python.exe
   PIP_EXE=C:\Users\HG\miniconda3\envs\ai_tools\Scripts\pip.exe
   ```

### 2.3. Still Not Working?
- Recreate the Conda environment:
  ```bash
  conda remove -n ai_tools --all -y
  python tools/setup_ai_conda.py
  ```
