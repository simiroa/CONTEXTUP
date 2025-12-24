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
    echo [INFO] Python not found. Installing automatically...
    
    :: Download Python Installer (3.11.9)
    echo Downloading Python 3.11.9...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download Python installer.
        pause
        exit /b 1
    )
    
    :: Install Python silently (System-wide, Add to Path)
    echo Installing Python... (This may check for Admin privileges)
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Cleanup
    if exist python_installer.exe del python_installer.exe
    
    :: Refresh Path (Hack: Restart script in new cmd to update path)
    echo Installation Complete. Restarting script...
    start "" "%~f0"
    exit /b
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
