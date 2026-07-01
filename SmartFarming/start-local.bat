@echo off
title SmartFarm Local Dev
cd /d "%~dp0"

echo Starting SmartFarm backend on http://localhost:8000 ...
start "SmartFarm Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

echo Waiting for backend to start...
timeout /t 4 /nobreak >nul

echo Starting SmartFarm frontend on http://localhost:3000 ...
start "SmartFarm Frontend" cmd /k "cd /d "%~dp0frontend" && npm start"

echo.
echo Both servers are starting in separate windows.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
pause
