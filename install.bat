@echo off
cd /d "%~dp0"
echo ==========================================
echo      ContextUp Installer Launcher
echo ==========================================

:: 1. Try to use embedded Python first (Preferred)
set PYTHON_EXE=ContextUp\tools\python\python.exe

if exist "%PYTHON_EXE%" (
    echo [INFO] Using embedded Python...
    goto :run_install
)

:: 2. Fallback to System Python (Bootstrapping)
echo [INFO] Embedded Python not found. Checking system Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] System Python found. Bootstrapping installation...
    set PYTHON_EXE=python
    goto :run_install
)

:: 3. Failure
echo.
echo [ERROR] Python not found!
echo         To install from source (Git Clone), you need Python 3.9+ installed on your system.
echo         Once installed, specific embedded Python will be downloaded automatically.
echo.
pause
exit /b 1

:run_install
"%PYTHON_EXE%" ContextUp/src/setup/install.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation script failed.
    pause
    exit /b 1
)
