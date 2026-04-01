@echo off
echo ===========================================
echo   GITHUB BACKUP (FULL VERSION)
echo ===========================================

:: 1. Git Init
echo [1/3] Initializing local Git repository...
git init
git add .
git commit -m "Backup of the Full Offline version before Cloud-only cleanup"

:: 2. Create Private Repo
echo.
echo [2/3] Creating private GitHub repository 'ws-whisper-full'...
:: --source=. инициализирует текущую папку как репозиторий
:: --private делает его закрытым
:: --push сразу отправляет код
gh repo create ws-whisper-full --private --source=. --remote=origin --push

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create or push to GitHub. 
    echo Please ensure you are logged in (run 'gh auth login').
) else (
    echo.
    echo SUCCESS: Full version is now safe in 'ws-whisper-full' (Private).
)

echo.
pause
