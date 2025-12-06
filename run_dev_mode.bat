@echo off
echo ========================================================
echo Starting Development Mode (Frontend + Backend)
echo ========================================================

echo 1. Starting Backend API (Flask)...
start "Backend API" cmd /k "run_web.bat"

echo 2. Starting Frontend Dev Server (Vite)...
cd frontend
start "Frontend Hot-Reload" cmd /k "npm run dev"

echo.
echo ========================================================
echo  Development Environment Started!
echo  Please access: http://localhost:5173
echo  (Do not use localhost:5000 for development)
echo ========================================================
echo.
pause