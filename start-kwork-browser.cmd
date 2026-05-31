@echo off
setlocal
set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" set CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" (
  echo Chrome not found.
  pause
  exit /b 1
)

set BOT_PROFILE=%LOCALAPPDATA%\KworkLeadChromeUserData
if not exist "%BOT_PROFILE%" mkdir "%BOT_PROFILE%"

set PROFILE_DIR=Default
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$localState=Join-Path $env:LOCALAPPDATA 'KworkLeadChromeUserData\Local State'; if (Test-Path $localState) { try { $data=Get-Content $localState -Raw | ConvertFrom-Json; if ($data.profile.last_used) { $data.profile.last_used } else { 'Default' } } catch { 'Default' } } else { 'Default' }"`) do set PROFILE_DIR=%%P

echo Opening Kwork bot Chrome profile without closing your regular Chrome...
start "" "%CHROME%" --user-data-dir="%BOT_PROFILE%" --profile-directory="%PROFILE_DIR%" --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run "https://kwork.ru/projects?c=11"

powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(12); do { try { Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 500 } } while ((Get-Date) -lt $deadline); exit 1"
if not "%ERRORLEVEL%"=="0" (
  echo Chrome started, but DevTools port 9222 is not available.
  echo Close only the Kwork bot Chrome window and try this script again.
  endlocal
  exit /b 1
)

echo Kwork Chrome is ready. If Kwork asks for login, sign in once in this bot window.
endlocal
