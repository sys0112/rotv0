@echo off
cd /d "%~dp0"

echo [1/2] Building lotto.exe ...
pyinstaller --onefile --console --name "lotto" --add-data "templates;templates" --hidden-import "flask" --hidden-import "jinja2" --hidden-import "werkzeug" --hidden-import "requests" --hidden-import "sqlite3" launcher.py
if %errorlevel% equ 0 (
    echo Build OK: dist\lotto.exe
) else (
    echo Build FAILED: lotto.exe
    pause
    exit /b 1
)

echo.
echo [2/2] Building 심심풀이.exe ...
pyinstaller --onefile --name "심심풀이" --exclude-module flask --exclude-module werkzeug --exclude-module jinja2 --exclude-module pytest menu.py
if %errorlevel% equ 0 (
    echo Build OK: dist\심심풀이.exe
) else (
    echo Build FAILED: 심심풀이.exe
)

pause
