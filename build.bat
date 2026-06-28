@echo off
cd /d "%~dp0"
pyinstaller --onefile --console --name "lotto" --add-data "templates;templates" --hidden-import "flask" --hidden-import "jinja2" --hidden-import "werkzeug" --hidden-import "requests" --hidden-import "sqlite3" launcher.py
if %errorlevel% equ 0 (
    echo Build OK: dist\lotto.exe
) else (
    echo Build FAILED
)
pause
