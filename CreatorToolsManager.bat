@echo off
cd /d "%~dp0"
if exist "tools\python\python.exe" (
    "tools\python\python.exe" "src\scripts\manager_gui.py"
) else (
    python "src\scripts\manager_gui.py"
)
pause
