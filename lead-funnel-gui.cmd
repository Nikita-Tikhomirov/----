@echo off
setlocal
set PYTHONPATH=%CD%\src
start "Kwork Lead Funnel" python -m app.gui
endlocal
