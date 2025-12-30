@echo off
cd /d "%~dp0"
echo ==========================================
echo      ContextUp Installer Launcher
echo ==========================================

:: Always use embedded Python (full version)
set EMBEDDED_PY=ContextUp\tools\python\python.exe
if not exist "%EMBEDDED_PY%" (
    echo [ERROR] Embedded Python not found.
    echo         Please use the full package that includes ContextUp\tools\python.
    pause
    exit /b 1
)

echo Using embedded Python...
"%EMBEDDED_PY%" ContextUp/src/setup/install.py

:check_result
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation script failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Launcher finished.
pause
