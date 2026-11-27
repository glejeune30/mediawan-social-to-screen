@echo off
rem Starts the Story Radar interface (web/, served by server.py) and opens it in the browser.
rem First run: creates a Python environment in %USERPROFILE%\.mediawan-radar (about 3 minutes);
rem it is only needed to refresh the data, the interface itself runs on plain Python.
cd /d "%~dp0"
set "VENV=%USERPROFILE%\.mediawan-radar\venv"
if not exist "%VENV%\Scripts\python.exe" (
    echo Creating the Python environment, about 3 minutes...
    python -m venv "%VENV%" || (echo Python 3 is needed: https://www.python.org/downloads/ & pause & exit /b 1)
    "%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
)
echo Story Radar: http://localhost:8600  (close this window to stop it)
start "" http://localhost:8600
"%VENV%\Scripts\python.exe" -X utf8 server.py --port 8600
