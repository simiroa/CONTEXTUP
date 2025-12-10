@echo off
cd /d "%~dp0"

REM Check if embedded python exists
if exist "tools\python\python.exe" (
    "tools\python\python.exe" "src\scripts\setup_console.py"
) else (
    echo Embedded Python not found. Trying system Python...
    python "src\scripts\setup_console.py"
)

pause
