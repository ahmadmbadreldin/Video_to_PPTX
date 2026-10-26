@echo off
setlocal
cd /d "%~dp0"

set "V2P_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%V2P_PYTHON%" (
    echo Virtual environment not found.
    echo Create it with: py -3.11 -m venv .venv
    echo Then install dependencies from requirements.txt.
    pause
    exit /b 1
)

"%V2P_PYTHON%" -m streamlit run "%~dp0src\video2pptx\app.py"
endlocal
