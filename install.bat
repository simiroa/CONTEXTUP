@echo off
cd /d "%~dp0"
echo ==================================================
echo      ContextUp: Minimal Installation
echo ==================================================
echo.
echo Installing core components...
python src/scripts/install_contextup.py
echo.
echo Done. You can now run 'ContextUpManager.bat'.
pause
