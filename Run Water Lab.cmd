@echo off
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo Please follow the installation steps in README.md first.
    pause
    exit /b 1
)
"%PYTHON%" main.py
if errorlevel 1 pause
