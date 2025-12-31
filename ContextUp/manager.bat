@echo off
setlocal
cd /d "%~dp0"

echo ContextUp Manager 실행 중...

:: Set PYTHONPATH to include src
set PYTHONPATH=%CD%\src;%PYTHONPATH%

:: Determine which python to use (Embedded first, then system)
if exist "tools\python\python.exe" (
    set "PYTHON_EXE=tools\python\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: Run the manager using the package mode
"%PYTHON_EXE%" -m manager.main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==========================================
    echo [ERROR] 매니저 실행 중 오류가 발생했습니다.
    echo.
    echo 원인: 필요한 패키지가 설치되지 않았을 수 있습니다.
    echo 해결: install.bat을 다시 실행하세요.
    echo ==========================================
    pause
)

endlocal
