@echo off
setlocal
cd /d "%~dp0.."
set "DEMO_DB=data\demo-%RANDOM%-%RANDOM%.db"
echo.
echo Myket Crawler - offline demonstration
echo No Myket requests will be sent.
echo.
where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher was not found. Install Python 3.9 or newer and retry.
    pause
    exit /b 1
)
py -3 src\main.py --demo --db "%DEMO_DB%"
if errorlevel 1 (
    echo Demo creation failed; see the error above.
    pause
    exit /b 1
)
for %%F in ("%DEMO_DB%") do set "REPORT_FILE=%%~dpnF-report.html"
echo Opening %REPORT_FILE%
start "" "%REPORT_FILE%"
echo Done. This demo contains synthetic apps only.
pause
