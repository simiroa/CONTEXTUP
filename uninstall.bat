@echo off
cd /d "%~dp0"
echo ==========================================
echo      ContextUp Uninstaller
echo ==========================================

:: 1. Try to use embedded Python first
set PYTHON_EXE=ContextUp\tools\python\python.exe

if exist "%PYTHON_EXE%" (
    echo [INFO] Using embedded Python...
    goto :run_uninstall
)

:: 2. Fallback to System Python
echo [INFO] Embedded Python not found. Checking system Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] System Python found. Bootstrapping uninstallation...
    set PYTHON_EXE=python
    goto :run_uninstall
)

:: 3. Failure
echo.
echo [ERROR] No Python environment found.
echo         Cannot run the cleanup script.
echo         Please manually delete the 'ContextUp' folder and registry keys.
echo.
pause
exit /b 1

:run_uninstall
:: Run the Python cleanup script
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

echo.
echo [INFO] Cleanup complete.
pause
