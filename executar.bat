@echo off
cd /d "%~dp0"
rem Abre o sistema. Nao precisa instalar nada alem do Python.
py -3 app.py
if errorlevel 1 pause
