from app import app, DatabaseServer, db

def add_sample_server():
    with app.app_context():
        # Check if we have any servers
        servers = DatabaseServer.query.all()
        print(f'Current number of servers: {len(servers)}')
        
        if len(servers) == 0:
            # Add a sample PostgreSQL server
            sample_server = DatabaseServer(
                name='Sample PostgreSQL Server',
                db_type='postgresql',
                host='localhost',
                port=5432,
                username='postgres',
                password='postgres'
            )
            db.session.add(sample_server)
            db.session.commit()
            print("Added sample PostgreSQL server")
            
            # Add a sample MySQL server
            sample_mysql = DatabaseServer(
                name='Sample MySQL Server',
                db_type='mysql',
                host='localhost',
                port=3306,
                username='root',
                password='root'
            )
            db.session.add(sample_mysql)
            db.session.commit()
            print("Added sample MySQL server")
        
        # Print all servers
        servers = DatabaseServer.query.all()
        print("\nConfigured Servers:")
        for server in servers:
            print(f'Server: {server.name}, Type: {server.db_type}, Host: {server.host}:{server.port}')

if __name__ == '__main__':
    add_sample_server()
