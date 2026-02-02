@echo off
chcp 65001 >nul
title Anitok Image Analyzer
echo.
echo ========================================
echo   Anitok Image Analyzer
echo   http://localhost:8085
echo ========================================
echo.

cd /d "%~dp0"

set STREAMLIT_PATH=C:\Users\닥터원츠\AppData\Local\Programs\Python\Python314\Scripts\streamlit.exe

if exist "%STREAMLIT_PATH%" (
    start "" "http://localhost:8085"
    "%STREAMLIT_PATH%" run image_analyzer_app.py --server.port 8085
) else (
    start "" "http://localhost:8085"
    python -m streamlit run image_analyzer_app.py --server.port 8085
)

pause
