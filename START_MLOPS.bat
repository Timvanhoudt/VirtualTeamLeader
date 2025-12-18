@echo off
echo ========================================
echo RefresCO v2 MLOps Platform
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "RefresCO Backend" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
start "RefresCO Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause >nul
