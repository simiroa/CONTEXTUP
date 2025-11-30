# Installation Guide for Creator Tools v2

This guide will help you install and set up the Creator Tools context menu extension on any Windows machine.

## Prerequisites

1.  **Windows 10 or 11**
2.  **NVIDIA GPU** (Recommended for AI features) with updated drivers.
3.  **Python 3.10+** installed and added to PATH.
4.  **Internet Connection** (Required to download tools during setup).

> **Note**: The `example` folder and large tools (Blender, FFmpeg, etc.) are **not included** in the installer to keep it lightweight.
> *   **Tools**: Will be downloaded automatically by the setup script.
> *   **Examples**: Please download the "Examples Pack" separately from the [Releases Page](https://github.com/simiroa/CONTEXTUP/releases) if needed.

## Installation Steps

### 1. Setup Python Environment

Open a terminal (PowerShell or Command Prompt) in this folder and run:

```powershell
# Create a virtual environment (optional but recommended)
python -m venv .venv

# Activate the virtual environment
# PowerShell:
.\.venv\Scripts\Activate.ps1
# Command Prompt:
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

> **Note:** If you have an NVIDIA GPU, ensure you install the CUDA-enabled version of PyTorch as specified in `requirements.txt`.

### 2. Setup AI Environment (Conda)

For advanced AI features (Background Removal, Upscaling), you need to set up a Conda environment.

1.  Install **Miniconda** or **Anaconda**.
2.  Run the setup script:

```powershell
python tools/setup_ai_conda.py
```

This will create an `ai_tools` environment with Python 3.10 and necessary AI libraries.

### 3. Configure Settings

The tool uses a `config/settings.json` file. If it doesn't exist, it will use defaults.
You can configure your API keys (for Gemini, etc.) using the **Manager GUI**.

### 4. Register Context Menu

To add the tools to your Windows Right-Click Menu, run:

```powershell
python manage.py register
```

You should see a "Registration complete" message.

### 5. Verify

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
