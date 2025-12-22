@echo off
cd /d "%~dp0"

set PYTHON_EXE=ContextUp\tools\python\python.exe

if not exist "%PYTHON_EXE%" (
    echo ==========================================
    echo [ERROR] 내장 파이썬을 찾을 수 없습니다.
    echo.
    echo 먼저 install.bat을 실행하여 설치를 완료하세요.
    echo ==========================================
    pause
    exit /b 1
)

echo ContextUp Manager 실행 중...
"%PYTHON_EXE%" "ContextUp\src\manager\main.py"

if %errorlevel% neq 0 (
    echo.
    echo ==========================================
    echo [ERROR] 매니저 실행 중 오류가 발생했습니다.
    echo.
    echo 원인: 필요한 패키지가 설치되지 않았을 수 있습니다.
    echo 해결: install.bat을 다시 실행하세요.
    echo ==========================================
    pause
)
