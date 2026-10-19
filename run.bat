@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=.venv\Scripts\python.exe"
) else (
    set "APP_PYTHON=py -3"
)

%APP_PYTHON% -c "import PyQt6" >nul 2>nul
if errorlevel 1 (
    echo PyQt6 is not installed for the selected Python interpreter.
    if exist ".venv\Scripts\python.exe" (
        echo First run: .venv\Scripts\python -m pip install -r requirements.txt
    ) else (
        echo First run: py -3 -m pip install -r requirements.txt
    )
    pause
    exit /b 1
)

%APP_PYTHON% main.py
endlocal
