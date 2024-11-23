from app import app, DatabaseServer, db
from datetime import datetime, timezone

def update_server():
    with app.app_context():
        # Update the existing PostgreSQL server with more realistic settings
        server = DatabaseServer.query.first()
        if server:
            server.name = "Local PostgreSQL"
            server.db_type = "postgresql"
            server.host = "localhost"
            server.port = 5432
            server.username = "postgres"  # Update with your actual PostgreSQL username
            server.password = "postgres"  # Update with your actual PostgreSQL password
            server.last_check = None
            server.last_error = None
            db.session.commit()
            print(f"Updated server: {server.name}")
        else:
            print("No server found to update")

if __name__ == '__main__':
    update_server()
