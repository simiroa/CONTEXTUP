# PowerShell:
.\.venv\Scripts\Activate.ps1
# Command Prompt:
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

> **Note:** If you have an NVIDIA GPU, ensure you install the CUDA-enabled version of PyTorch as specified in `requirements.txt`.

### 2. Restore Tools & Environment (Vital)

If you downloaded the **Minimal Backup** version, you need to restore the environment and tools.

1.  **Run the Master Setup**:
    ```powershell
    python setup_all.py
    ```
    This will:
    *   Download and configure the **Python Environment** (`tools/python`).
    *   Download external tools like **FFmpeg, ExifTool, Real-ESRGAN** (`tools/ffmpeg`, etc.).
    *   Download necessary AI models (if any).

2.  **Verify Setup**:
    Check if `tools/python/python.exe` exists. This is the engine that runs ContextUp.

### 3. Setup AI Environment (Optional)

For advanced AI features (Background Removal, Upscaling), you need to set up a Conda environment.

1.  Install **Miniconda** or **Anaconda**.
2.  Run the setup script:

```powershell
python tools/setup_ai_conda.py
```

This will create an `ai_tools` environment with Python 3.10 and necessary AI libraries.

### 4. Configure Settings

The tool uses a `config/settings.json` file. If it doesn't exist, it will use defaults.
You can configure your API keys (for Gemini, etc.) using the **Manager GUI**.

### 5. Register Context Menu

To add the tools to your Windows Right-Click Menu, run:

```powershell
python manage.py register
```

You should see a "Registration complete" message.

### 6. Verify

Right-click on any file or folder. You should see a **"Creator Tools"** menu item.

## Moving the Folder

If you move this project folder to a new location:
1.  Open a terminal in the *new* location.
2.  Run `python manage.py register` again.
    *   This will automatically update the registry paths to point to the new location.

## Uninstallation

To remove the context menu:

```powershell
python manage.py unregister
```

## Troubleshooting

### Tray Agent Issues
If the Tray Agent icon does not appear:
1. Open **Manager GUI**.
2. Go to **Settings**.
3. In "Python Environment", ensure the path is valid or select "Custom" to point to your System Python if needed.
4. Click **"Test Connection"** to verify dependencies (`pystray`, `Pillow`, `pywin32`).
