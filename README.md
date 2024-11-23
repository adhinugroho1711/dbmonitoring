# Database Monitoring Application

A Flask-based web application for monitoring multiple database servers (PostgreSQL, MySQL, MariaDB) in real-time. Track system metrics, database performance, and active queries through an intuitive web interface.

## Features

- **Multi-Database Support**
  - PostgreSQL
  - MySQL
  - MariaDB

- **Real-Time Monitoring**
  - CPU Usage
  - Memory Usage
  - Disk Usage
  - Active Connections
  - Cache Hit Ratio
  - Active Queries

- **User Management**
  - Role-based access control (Admin/User)
  - Secure authentication
  - Activity logging

- **Server Management**
  - Add/Edit/Delete database servers
  - Test server connections
  - View server metrics
  - Track query history

## Quick Installation

### For Linux/macOS Users

1. Clone the repository:
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

4. Start the application:
   ```bash
   source venv/bin/activate
   python -m flask run
   ```

### For Windows Users

1. Clone the repository:
   ```cmd
   git clone https://github.com/adhinugroho1711/dbmonitoring.git
   cd dbmonitoring
   ```

2. Run the installation script:
   ```cmd
   install_windows.bat
   ```

3. Start the application:
   ```cmd
   venv\Scripts\activate
   python -m flask run
   ```

## Manual Installation

If you prefer to install manually:

1. Create and activate virtual environment:
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment:
   ```bash
   # Create instance directory
   mkdir instance
   
   # Create .env file
   echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')" > instance/.env
   echo "DATABASE_URL=sqlite:///dbmonitor.db" >> instance/.env
   ```

4. Initialize database:
   ```bash
   flask db upgrade
   python create_admin.py
   ```

## Default Credentials

After installation, you can log in with:
- Username: admin
- Password: admin

**Important**: Change the admin password after first login!

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- PostgreSQL, MySQL, or MariaDB server(s) to monitor

## Configuration

### Database Server Configuration

1. PostgreSQL:
   - Enable `pg_stat_statements` extension
   - Grant monitoring privileges to database user

2. MySQL/MariaDB:
   - Grant PROCESS, REPLICATION CLIENT privileges
   - Enable performance schema

### Environment Variables

Key environment variables in `instance/.env`:
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: SQLite database URL
- Additional configurations can be added as needed

## Development

1. Running tests:
   ```bash
   pytest
   ```

2. Code coverage:
   ```bash
   pytest --cov=.
   ```

## Security Considerations

1. Change default admin password immediately
2. Use secure database credentials
3. Enable HTTPS in production
4. Keep dependencies updated
5. Regular security audits
6. Proper firewall configuration

## Troubleshooting

1. Database Connection Issues:
   - Verify database credentials
   - Check network connectivity
   - Ensure proper privileges

2. Installation Problems:
   - Check Python version compatibility
   - Verify pip installation
   - Check system permissions

3. Application Errors:
   - Check application logs
   - Verify environment variables
   - Ensure database migrations are up to date

## Support and Contribution

- Report issues on [GitHub Issues](https://github.com/adhinugroho1711/dbmonitoring/issues)
- Submit pull requests for improvements
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version History

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed version history and changes.
