@echo off
echo Starting CLIP Image Search...

:: Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate

:: Start the application
echo Starting server...
echo Server will be available at http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 