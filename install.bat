@echo off
cd /d "%~dp0"
echo ==========================================
echo      ContextUp Installer Launcher
echo ==========================================

:: Check for embedded Python first
set EMBEDDED_PY=ContextUp\tools\python\python.exe
if exist "%EMBEDDED_PY%" (
    echo Using embedded Python...
    "%EMBEDDED_PY%" ContextUp/src/setup/install.py
    goto :check_result
)

:: Fallback to system Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

python ContextUp/src/setup/install.py

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
