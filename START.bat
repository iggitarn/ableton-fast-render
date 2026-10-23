@echo off
cd /d "%~dp0"
python -m afr check
echo.
echo Commands:  python -m afr check ^| boost ^| reset
echo.
if "%1"=="" (
  echo Usage examples:
  echo   START.bat check
  echo   START.bat boost
  echo   START.bat reset
  pause
  exit /b 0
)
python -m afr %*
pause
