@echo off
cd /d "%~dp0"

echo Building lotto.exe ...
pyinstaller --onefile --console --name "lotto" --add-data "templates;templates" --hidden-import "flask" --hidden-import "jinja2" --hidden-import "werkzeug" --hidden-import "werkzeug.security" --hidden-import "requests" --hidden-import "sqlite3" --hidden-import "license" launcher.py
if %errorlevel% equ 0 (
    echo Build OK: dist\lotto.exe
) else (
    echo Build FAILED: lotto.exe
)

pause
