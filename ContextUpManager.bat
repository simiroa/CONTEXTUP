@echo off
cd /d "%~dp0"

REM 1. Check for Embedded Python (Primary)
if exist "tools\python\python.exe" (
    echo [Using Embedded Python]
    "tools\python\python.exe" "src\scripts\manager_gui.py"
    goto :EOF
)

REM 2. Fallback to Virtual Environment (Legacy)
if exist "tools\contextup_venv\Scripts\python.exe" (
    echo [Using Virtual Environment]
    "tools\contextup_venv\Scripts\python.exe" "src\scripts\manager_gui.py"
    goto :EOF
)

REM 3. Fallback to System Python
echo [Using System Python]
python "src\scripts\manager_gui.py"
pause
