#!/usr/bin/env bash
# Instalação no Linux/macOS. Precisa do Tkinter (Ubuntu: sudo apt install python3-tk)
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
"$PY" -c "import tkinter" || { echo "Tkinter não encontrado (Ubuntu: sudo apt install python3-tk)"; exit 1; }
"$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tests/teste_regras.py
echo "Instalação concluída! Rode ./executar.sh"
