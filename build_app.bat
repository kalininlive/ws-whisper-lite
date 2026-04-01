@echo off
setlocal enabledelayedexpansion

echo ===========================================
echo   DICTATION APP - LIGHT BUILD (CLOUD ONLY)
echo ===========================================

:: 1. Building Code (Nuitka)
echo [1/2] Compiling code with Nuitka (Light Mode)...
:: УБРАНЫ --include-data-dir для bin и models
python -m nuitka --standalone --show-progress --disable-console --windows-icon-from-ico=assets/icon.ico src/main.py --output-dir=dist --output-filename=DictationApp.exe

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Nuitka build failed.
    pause
    exit /b
)

:: 2. Packaging into Installer (Inno Setup)
echo.
echo [2/2] Creating Setup.exe with Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo.
    echo WARNING: Inno Setup not found. Final Setup.exe not created.
) else (
    %ISCC% installer.iss
    if !ERRORLEVEL! EQU 0 (
        echo.
        echo SUCCESS: Light_WS_Whisper_Setup.exe created in /dist/!
    )
)

echo.
pause
