@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Instalando o Sistema de Hotel ===

set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY (where python >nul 2>nul && set PY=python)
if not defined PY (
    echo Python nao encontrado. Instale em https://www.python.org/downloads/
    echo e marque a opcao "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/3] Criando ambiente virtual .venv ...
%PY% -m venv .venv || goto erro

echo [2/3] Instalando dependencias ...
.venv\Scripts\python -m pip install --upgrade pip >nul
.venv\Scripts\python -m pip install -r requirements.txt || goto erro

echo [3/3] Testando as regras do sistema ...
.venv\Scripts\python tests\teste_regras.py || goto erro

echo.
echo Instalacao concluida! Para abrir o sistema, de dois cliques em executar.bat
pause
exit /b 0

:erro
echo.
echo Ocorreu um erro na instalacao. Veja a mensagem acima.
pause
exit /b 1
