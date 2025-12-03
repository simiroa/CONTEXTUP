@echo off
cd /d "%~dp0"

REM Check if embedded python has tkinter
"tools\python\python.exe" -c "import tkinter" >nul 2>&1
if %errorlevel% equ 0 (
    "tools\python\python.exe" "src\scripts\manager_gui.py"
) else (
    echo Embedded Python missing Tkinter, trying system Python...
    python "src\scripts\manager_gui.py"
)
pause
