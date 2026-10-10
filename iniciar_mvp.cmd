@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Ambiente Python nao encontrado. Consulte README.md.
  pause
  exit /b 1
)
echo Rota do Diploma - abra http://localhost:8501
"venv\Scripts\python.exe" -m streamlit run app.py --server.address=127.0.0.1
