@echo off
setlocal

:: Set the current directory to the script location
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Please run setup.bat first.
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate

:: Create a log file with timestamp
set "LOG_FILE=service_log_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.txt"
set "LOG_FILE=%LOG_FILE: =0%"

:: Start the application with logging
echo Starting CLIP Image Search Service at %date% %time% > "%LOG_FILE%"
echo Server will be available at http://localhost:8000 >> "%LOG_FILE%"

:: Run the server without --reload flag for production
uvicorn backend.main:app --host 0.0.0.0 --port 8000 >> "%LOG_FILE%" 2>&1 