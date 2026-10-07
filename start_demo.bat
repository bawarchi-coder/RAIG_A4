@echo off
rem Starts everything for the demo, each in its own window:
rem   Vendor B demo screening service  http://127.0.0.1:8001
rem   Fairness API (Swagger page)      http://127.0.0.1:8000/docs
rem   Standalone app                   http://127.0.0.1:8501
rem Close the three windows to stop.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The virtual environment is missing. Run these two commands first:
  echo   python -m venv .venv
  echo   .venv\Scripts\python -m pip install -r requirements.txt
  pause
  exit /b 1
)
start "Vendor B (demo screener)" .venv\Scripts\python.exe demo\screener_service.py
start "Fairness API" .venv\Scripts\python.exe -m uvicorn integration.api:app --host 127.0.0.1 --port 8000
start "Fairness app" .venv\Scripts\python.exe -m streamlit run app.py
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8501/?run=screener_a"
start "" "http://127.0.0.1:8000/docs"
