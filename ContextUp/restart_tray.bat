@echo off
echo Killing all python processes...
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe

cd /d "%~dp0"
echo Starting Tray Agent...
start /B python src/tray/agent.py
echo Done.
