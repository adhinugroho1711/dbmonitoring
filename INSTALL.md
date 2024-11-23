# Installation Guide

This guide will help you install and run the Database Monitoring Application on your system.

## Prerequisites

1. Python 3.8 or higher
2. pip (Python package installer)
3. Git (optional, for cloning the repository)

## Installation Steps

### For Linux/macOS Users

1. Clone or download the repository:
   ```bash
   git clone https://github.com/adhinugroho1711/dbmonitoring.git
   cd dbmonitoring
   ```

2. Make the installation script executable:
   ```bash
   chmod +x install_unix.sh
   ```

3. Run the installation script:
   ```bash
   ./install_unix.sh
   ```

### For Windows Users

1. Clone or download the repository:
   ```cmd
   git clone https://github.com/adhinugroho1711/dbmonitoring.git
   cd dbmonitoring
   ```

2. Run the installation script by double-clicking `install_windows.bat` or running:
   ```cmd
   install_windows.bat
   ```

## Running the Application

### Linux/macOS
1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Start the application:
   ```bash
   python -m flask run
   ```

### Windows
1. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```

2. Start the application:
   ```cmd
   python -m flask run
   ```

## Default Credentials

After installation, you can log in with these default credentials:
- Username: admin
- Password: admin

**Important**: Please change the admin password after your first login for security purposes.

## Troubleshooting

1. If you get a "Permission denied" error on Linux/macOS:
   ```bash
   chmod +x install_unix.sh
   ```

2. If Python is not found on Windows, ensure it's added to your PATH environment variable.

3. If you encounter database errors:
   ```bash
   python recreate_db.py
   ```

4. For any other issues, please check the GitHub issues page or create a new issue.

## Security Notes

1. Change the default admin password immediately after installation
2. Keep your `.env` file secure and never share it
3. Use HTTPS in production environments
4. Regularly update dependencies for security patches

## Support

If you encounter any issues or need help, please:
1. Check the [GitHub Issues](https://github.com/adhinugroho1711/dbmonitoring/issues)
2. Create a new issue with detailed information about your problem
3. Include your OS and Python version when reporting issues
