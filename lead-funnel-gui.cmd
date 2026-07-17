@echo off
setlocal
chcp 65001 >nul
set PYTHONPATH=%CD%\src
set PYTHONIOENCODING=utf-8
start "Kwork Lead Funnel" python -m app.gui
endlocal
