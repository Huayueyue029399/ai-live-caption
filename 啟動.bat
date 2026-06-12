@echo off
chcp 65001 >nul
title Pro 即時字幕系統 - 安裝啟動

echo ========================================
echo    正在安裝所需套件，請稍候...
echo ========================================
echo.

:: 安裝必要套件
pip install vosk pyaudio jieba numpy

if %errorlevel% neq 0 (
    echo.
    echo [錯誤] 安裝失敗，請檢查網路連線後重試。
    pause
    exit /b 1
)

echo.
echo ========================================
echo    安裝完成，啟動應用程式...
echo ========================================
echo.

:: 啟動主程式
cd /d "%~dp0"
python "%~dp0pro_caption_app.py"

pause
