@echo off
setlocal
set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" set CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" (
  echo Chrome not found.
  pause
  exit /b 1
)

set PROFILE=%LOCALAPPDATA%\KworkLeadChrome
if not exist "%PROFILE%" mkdir "%PROFILE%"

start "" "%CHROME%" --user-data-dir="%PROFILE%" --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run --disable-default-apps "https://kwork.ru/projects?c=11"
echo Chrome started for Kwork monitoring.
endlocal
