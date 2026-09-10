@echo off
title Advocate Mukesh Singh Rathod - Live Legal Chambers
cd /d %~dp0
echo ========================================================
echo  Advocate Mukesh Singh Rathod - Live Server Launcher
echo ========================================================
echo [1/2] Starting Flask Local Server...
start "Flask Backend" cmd /c "python app.py"
echo Waiting for server to initialize...
timeout /t 3 /nobreak >nul
echo [2/2] Creating Public Live Internet Link...
echo.
echo Share the https://...trycloudflare.com link to open anywhere!
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
