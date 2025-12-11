@echo off
cd /d "%~dp0"
echo ==================================================
echo      ContextUp: Minimal Installation
echo ==================================================
echo.
echo Installing core components...

REM Use embedded Python first, then system Python
if exist "tools\python\python.exe" (
    "tools\python\python.exe" "src\scripts\install_contextup.py"
) else (
    python "src\scripts\install_contextup.py"
)

echo.
echo Done. You can now run 'ContextUpManager.bat'.
pause
