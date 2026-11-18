@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call instalar.bat
.venv\Scripts\python app.py
if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir a versao moderna. Abrindo a versao classica...
    .venv\Scripts\python app_classico.py
    pause
)
