@echo off
echo ========================================
echo   AI Message Composer - Starting Server
echo ========================================
echo.
echo Checking Neo4j connection...
echo.

cd /d "%~dp0server"
python main.py

pause

