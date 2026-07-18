@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
"C:\Users\user\AppData\Local\Programs\Python\Python310\pythonw.exe" -m app.main mobile-control
