@echo off
REM One-click starter for SIH74 Hyperlocal Weather Intelligence demo.
REM Opens API (port 8000) + Dashboard (port 8501) in two windows.
cd /d "%~dp0"
echo Starting SIH74 API server...
start "SIH74-API (port 8000)" cmd /k "python -m src.main"
timeout /t 7 >nul
echo Starting SIH74 Dashboard...
start "SIH74-Dashboard (port 8501)" cmd /k "python -m streamlit run dashboard/app.py"
echo.
echo Dashboard: http://localhost:8501  (open the BLOCK page)
echo API docs:  http://localhost:8000/docs
echo.
pause
