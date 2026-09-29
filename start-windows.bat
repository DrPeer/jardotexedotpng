@echo off
chcp 65001 >nul
title mObywatel - wersja web (kopia pogladowa)
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Nie znaleziono Pythona. Zainstaluj Python 3 z https://www.python.org/downloads/
  echo   i zaznacz opcje "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)
echo.
echo   Uruchamiam aplikacje... Zostaw to okno otwarte podczas korzystania z aplikacji.
echo.
start "" http://localhost:8000
python server.py --port 8000
pause
