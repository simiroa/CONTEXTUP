@echo off
cd /d "%~dp0"

echo ==================================================
echo      ContextUp Uninstaller
echo ==================================================
echo.

REM 1. Run Python Cleanup Script (Registry & Cache)
REM Try Venv first, then system. We need ANY python to run the script.
if exist "tools\contextup_venv\Scripts\python.exe" (
    "tools\contextup_venv\Scripts\python.exe" "src\scripts\uninstall_contextup.py"
) else (
    python "src\scripts\uninstall_contextup.py"
)

REM Check if user cancelled (python script returns 1)
if %errorlevel% neq 0 (
    echo.
    echo Uninstall cancelled or failed.
    pause
    exit /b
)

echo.
echo --- Removing Environments ---

REM 2. Remove Virtual Environment
if exist "tools\contextup_venv" (
    echo Removing Virtual Environment...
    rmdir /s /q "tools\contextup_venv"
)

REM 3. Remove Conda Environment (Optional AI)
if exist "tools\conda" (
    echo Removing AI Environment...
    rmdir /s /q "tools\conda"
)

echo.
echo [SUCCESS] ContextUp has been uninstalled.
echo (Configuration files in 'config' were kept safe)
echo.
pause
