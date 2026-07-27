@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════╗
echo ║    经济学人 · 每日阅读器       ║
echo ╚══════════════════════════════════╝
echo.

:menu
echo [1] 下载最新期刊 (最近4期)
echo [2] 下载全部期刊
echo [3] 提取文章
echo [4] 下载 + 提取 + 开始阅读
echo [5] 开始阅读 (跳过下载)
echo [0] 退出
echo.
set /p choice="请选择 (0-5): "

if "%choice%"=="1" goto download
if "%choice%"=="2" goto download_all
if "%choice%"=="3" goto extract
if "%choice%"=="4" goto full
if "%choice%"=="5" goto read
if "%choice%"=="0" goto end
echo 无效选择，请重试。
goto menu

:download
echo.
echo === 下载最新4期 ===
python downloader.py
echo.
pause
goto menu

:download_all
echo.
echo === 下载全部 ===
python downloader.py --all
echo.
pause
goto menu

:extract
echo.
echo === 提取文章 ===
python extractor.py
echo.
pause
goto menu

:full
echo.
echo === 第1步: 下载 ===
python downloader.py
echo.
echo === 第2步: 提取 ===
python extractor.py
echo.
goto read

:read
echo.
echo === 启动阅读器 ===
start "" python server.py
timeout /t 2 >nul
goto end

:end
