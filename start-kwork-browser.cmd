@echo off
setlocal
set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" set CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME%" (
  echo Chrome not found.
  pause
  exit /b 1
)

echo Preparing logged-in Kwork Chrome profile copy...
powershell -NoProfile -Command "Get-Process chrome -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() | Out-Null }; Start-Sleep -Seconds 4"
taskkill /IM chrome.exe /F >nul 2>nul
timeout /t 1 /nobreak >nul

set SOURCE_PROFILE=%LOCALAPPDATA%\Google\Chrome\User Data
set BOT_PROFILE=%LOCALAPPDATA%\KworkLeadChromeUserData
set PROFILE_DIR=Default
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$localState=Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Local State'; if (Test-Path $localState) { try { $data=Get-Content $localState -Raw | ConvertFrom-Json; if ($data.profile.last_used) { $data.profile.last_used } else { 'Default' } } catch { 'Default' } } else { 'Default' }"`) do set PROFILE_DIR=%%P
echo Copying Chrome profile: %PROFILE_DIR%
if not exist "%BOT_PROFILE%" mkdir "%BOT_PROFILE%"
copy /Y "%SOURCE_PROFILE%\Local State" "%BOT_PROFILE%\Local State" >nul
robocopy "%SOURCE_PROFILE%\%PROFILE_DIR%" "%BOT_PROFILE%\%PROFILE_DIR%" /MIR /R:1 /W:1 /XD "Cache" "Code Cache" "GPUCache" "Service Worker\CacheStorage" "Service Worker\ScriptCache" "ShaderCache" "GrShaderCache" "DawnCache" "Crashpad" /XF "LOCK" "SingletonLock" "SingletonSocket" "SingletonCookie" >nul
if %ERRORLEVEL% GEQ 8 (
  echo Failed to copy Chrome profile for Kwork monitoring.
  endlocal
  exit /b 1
)

echo Starting Kwork bot Chrome profile: %BOT_PROFILE%\%PROFILE_DIR%
start "" "%CHROME%" --user-data-dir="%BOT_PROFILE%" --profile-directory="%PROFILE_DIR%" --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run "https://kwork.ru/projects?c=11"

powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(12); do { try { Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 500 } } while ((Get-Date) -lt $deadline); exit 1"
if not "%ERRORLEVEL%"=="0" (
  echo Chrome started, but DevTools port 9222 is not available.
  endlocal
  exit /b 1
)

echo Chrome started with your default profile for Kwork monitoring.
endlocal
