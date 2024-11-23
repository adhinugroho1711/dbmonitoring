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

## Prerequisites

- Python 3.8+
- PostgreSQL, MySQL, or MariaDB server(s)
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adhinugroho1711/dbmonitoring.git
   cd dbmonitoring
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///dbmonitor.db
   ```

5. Initialize the database:
   ```bash
   python -m flask db upgrade
   python create_admin.py
   ```

## Configuration

1. Default admin credentials:
   - Username: admin
   - Password: admin

2. Database server configuration:
   - Host: Your database server host
   - Port: Database port (PostgreSQL: 5432, MySQL: 3306)
   - Username: Database user with monitoring privileges
   - Password: Database user password

## Usage

1. Start the application:
   ```bash
   python -m flask run
   ```

2. Access the web interface:
   - URL: http://127.0.0.1:5000
   - Log in with admin credentials
   - Add database servers to monitor
   - View real-time metrics and active queries

## Security Considerations

1. Change the default admin password after first login
2. Use environment variables for sensitive information
3. Regularly update dependencies
4. Use secure database credentials with minimal required privileges
5. Enable HTTPS in production

## Development

1. Running tests:
   ```bash
   pytest
   ```

2. Code coverage:
   ```bash
   pytest --cov=.
   ```

## Project Structure

```
dbmonitoring/
├── app.py                 # Main application file
├── db_monitor.py         # Database monitoring logic
├── monitor_service.py    # Monitoring service
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   └── ...
├── static/             # Static files (CSS, JS)
├── migrations/         # Database migrations
├── tests/             # Test files
└── requirements.txt    # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

- v1.0.0 (2024-11-23)
  - Initial release
  - Basic monitoring features
  - Multi-database support
  - User management
  - Real-time metrics display

## Acknowledgments

- Flask and its extensions
- Chart.js for metrics visualization
- Bootstrap for UI components
