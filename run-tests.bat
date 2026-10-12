@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
python tools\check_conventions.py
if errorlevel 1 exit /b 1
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
python guitests\run_checks.py
exit /b %errorlevel%
