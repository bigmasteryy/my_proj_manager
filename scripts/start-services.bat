@echo off
setlocal

set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-services.ps1" %*

if errorlevel 1 (
  echo.
  echo Start script failed. Please check the output above.
  exit /b 1
)

endlocal
