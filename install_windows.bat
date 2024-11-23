@echo off
echo Installing Database Monitoring Application...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed. Please install Python first.
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip is required but not installed. Please install pip first.
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist instance\.env (
    echo Creating .env file...
    if not exist instance mkdir instance
    python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(16))" > instance\.env
    echo DATABASE_URL=sqlite:///dbmonitor.db >> instance\.env
)

REM Initialize database
echo Initializing database...
python -m flask db upgrade

REM Create admin user
echo Creating admin user...
python create_admin.py

echo Installation complete!
echo To start the application:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run the application: python -m flask run
pause
