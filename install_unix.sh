#!/bin/bash

echo "Installing Database Monitoring Application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f instance/.env ]; then
    echo "Creating .env file..."
    mkdir -p instance
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')" > instance/.env
    echo "DATABASE_URL=sqlite:///dbmonitor.db" >> instance/.env
fi

# Initialize database
echo "Initializing database..."
flask db upgrade

# Create admin user
echo "Creating admin user..."
python create_admin.py

echo "Installation complete!"
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the application: python -m flask run"
