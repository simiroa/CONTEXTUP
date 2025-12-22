@echo off
cd /d "%~dp0"
echo ==========================================
echo      ContextUp Uninstaller
echo ==========================================

:: Determine Python to use
set "PYTHON_EXE=python"
if exist "ContextUp\tools\python\python.exe" (
    set "PYTHON_EXE=ContextUp\tools\python\python.exe"
)

:: Run the Python cleanup script (Nested in ContextUp)
"%PYTHON_EXE%" ContextUp/src/setup/uninstall.py
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Uninstallation cancelled or failed.
    pause
    exit /b 1
)

echo.
echo Attempting to remove local tools (Python environment)...
rmdir /s /q ContextUp\tools\python 2>nul
if exist ContextUp\tools\python (
    echo [WARN] Could not fully remove tools\python (files might be in use).
    echo Please manually delete the "ContextUp\tools" folder to complete removal.
) else (
    echo [SUCCESS] Environment removed.
)

pause
