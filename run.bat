@echo off
title PLN Electricity Tracker Cloud
echo ========================================================
echo   ⚡ Menjalankan PLN Electricity Tracker Web App
echo ========================================================
echo.

:: Cek apakah streamlit dan dependensi sudah terinstall
python -c "import streamlit, pandas, plotly, pymongo" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Menginstal dependensi yang dibutuhkan...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Gagal menginstal dependensi. Pastikan Python dan pip terpasang.
        pause
        exit /b %errorlevel%
    )
)

echo [INFO] Menjalankan server Streamlit di http://localhost:8501 ...
echo.
python -m streamlit run app.py

pause
