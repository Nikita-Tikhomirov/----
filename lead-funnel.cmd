@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"

if "%~1"=="" (
  echo.
  echo Telegram Lead Funnel
  echo.
  echo Usage:
  echo   lead-funnel.cmd scan
  echo   lead-funnel.cmd watch
  echo   lead-funnel.cmd approvals
  echo   lead-funnel.cmd orders list
  echo.
  echo Common:
  echo   lead-funnel.cmd scan
  echo.
  pause
  exit /b 0
)

python -m app.main %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Command failed with exit code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%
