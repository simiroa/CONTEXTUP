@echo off
cd /d "%~dp0"

echo ==================================================
echo      ContextUp Uninstaller
echo ==================================================
echo.

REM 1. Run Python Cleanup Script (Registry & Cache)
REM Use the Embedded Python if available
if exist "tools\python\python.exe" (
    "tools\python\python.exe" "src\scripts\uninstall_contextup.py"
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

REM 2. Remove Unified Python Environment
if exist "tools\python" (
    echo Removing Local Python...
    rmdir /s /q "tools\python"
)

REM 3. Remove Legacy Environments (Cleanup)
if exist "tools\contextup_venv" (
    echo Removing Legacy Venv...
    rmdir /s /q "tools\contextup_venv"
)
if exist "tools\conda" (
    echo Removing Legacy AI Conda Env...
    rmdir /s /q "tools\conda"
)

echo.
echo [SUCCESS] ContextUp has been uninstalled.
echo (Configuration files in 'config' were kept safe)
echo.
pause
