@echo off
setlocal
set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" set CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" (
  echo Chrome not found.
  pause
  exit /b 1
)

powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if "%ERRORLEVEL%"=="0" (
  start "" "%CHROME%" "https://kwork.ru/projects?c=11"
  echo Chrome DevTools already running for Kwork monitoring.
  endlocal
  exit /b 0
)

echo Restarting Chrome with your default profile and DevTools port 9222...
powershell -NoProfile -Command "Get-Process chrome -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() | Out-Null }; Start-Sleep -Seconds 4"
taskkill /IM chrome.exe /F >nul 2>nul
timeout /t 1 /nobreak >nul

set PROFILE=%LOCALAPPDATA%\Google\Chrome\User Data
start "" "%CHROME%" --user-data-dir="%PROFILE%" --profile-directory=Default --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run "https://kwork.ru/projects?c=11"

powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(12); do { try { Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 500 } } while ((Get-Date) -lt $deadline); exit 1"
if not "%ERRORLEVEL%"=="0" (
  echo Chrome started, but DevTools port 9222 is not available.
  endlocal
  exit /b 1
)

echo Chrome started with your default profile for Kwork monitoring.
endlocal
