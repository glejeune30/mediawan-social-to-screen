@echo off
rem Starts the Story Radar prototype (Streamlit) and opens it in the browser.
rem First run: creates a Python environment in %USERPROFILE%\.mediawan-radar (about 3 minutes).
cd /d "%~dp0"
set "VENV=%USERPROFILE%\.mediawan-radar\venv"
if not exist "%VENV%\Scripts\python.exe" (
    echo Creating the Python environment, about 3 minutes...
    python -m venv "%VENV%" || (echo Python 3 is needed: https://www.python.org/downloads/ & pause & exit /b 1)
    "%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
)
echo Story Radar: http://localhost:8501  (close this window to stop the app)
start "" http://localhost:8501
"%VENV%\Scripts\python.exe" -m streamlit run app\streamlit_app.py --server.port 8501 --server.address localhost --server.headless true
