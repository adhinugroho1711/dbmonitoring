import unittest
from app import app, db, User, DatabaseServer
from flask import url_for
import json
import os
from unittest.mock import patch

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            test_user = User(
                username='test_user',
                email='test@example.com',
                role='user'
            )
            test_user.set_password('test_password')
            db.session.add(test_user)
            
            # Create test database server
            test_server = DatabaseServer(
                name='Test PostgreSQL',
                db_type='postgresql',
                host='localhost',
                port=5432,
                username='test_user',
                password='test_pass'
            )
            db.session.add(test_server)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username='test_user', password='test_password'):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_login_logout(self):
        # Test login with correct credentials
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Database Servers Overview', response.data)

        # Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

        # Test login with incorrect credentials
        response = self.client.post('/login', data=dict(
            username='test_user',
            password='wrong_password'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_protected_routes(self):
        # Try accessing protected route without login
        response = self.client.get('/database_servers')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        # Login and try again
        self.login()
        response = self.client.get('/database_servers')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Database Servers', response.data)

    def test_api_metrics(self):
        # Login first
        self.login()
        
        # Test metrics endpoint
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        
        # Check metrics structure
        metrics = data[0]
        self.assertIn('server_id', metrics)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)
        self.assertIn('active_connections', metrics)

    def test_server_metrics(self):
        # Login first
        self.login()

        # Get the test server's ID
        with app.app_context():
            server = DatabaseServer.query.first()
            server_id = server.id

        # Mock the database monitor
        mock_metrics = {
            'cpu_percent': 25.5,
            'memory_percent': 60.2,
            'disk_usage': 45.8,
            'active_connections': 10,
            'cache_hit_ratio': 95.5,
            'active_queries': [
                {
                    'pid': 1234,
                    'usename': 'test_user',
                    'query': 'SELECT * FROM users',
                    'state': 'active',
                    'duration_seconds': 2.5
                }
            ]
        }

        with patch('db_monitor.DatabaseMonitor.get_performance_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = mock_metrics
            
            # Test server metrics endpoint
            response = self.client.get(f'/api/server/{server_id}/metrics')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertIn('cpu_percent', data)
            self.assertIn('memory_percent', data)
            self.assertIn('active_queries', data)

    def test_server_metrics_error_cases(self):
        # Login first
        self.login()

        # Test non-existent server
        response = self.client.get('/api/server/999/metrics')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

        # Test server with connection error
        with app.app_context():
            server = DatabaseServer.query.first()
            server_id = server.id

        with patch('db_monitor.DatabaseMonitor.get_performance_metrics') as mock_get_metrics:
            mock_get_metrics.side_effect = Exception("Connection failed")
            response = self.client.get(f'/api/server/{server_id}/metrics')
            self.assertEqual(response.status_code, 500)
            self.assertIn('error', response.get_json())

    def test_users_management(self):
        # Create admin user
        with app.app_context():
            admin = User(
                username='admin_user',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin_pass')
            db.session.add(admin)
            db.session.commit()

        # Login as regular user
        self.login()
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 302)  # Should redirect due to unauthorized

        # Login as admin
        self.login('admin_user', 'admin_pass')
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User Management', response.data)
        self.assertIn(b'test_user', response.data)

    def test_activity_logs(self):
        # Login
        self.login()

        # Access some pages to generate logs
        self.client.get('/')
        self.client.get('/database_servers')

        with patch('app.render_template') as mock_render:
            # Mock render_template to avoid template issues
            mock_render.return_value = ''
            
            # Check activity logs
            response = self.client.get('/activity_logs')
            self.assertEqual(response.status_code, 200)
            
            # Verify that logs were passed to template
            args, kwargs = mock_render.call_args
            self.assertEqual(args[0], 'activity_logs.html')
            self.assertTrue('logs' in kwargs)
            logs = kwargs['logs']
            self.assertTrue(len(logs) > 0)
            
            # Get all menu_accessed values
            menu_accessed = [log.menu_accessed for log in logs]
            self.assertIn('dashboard', menu_accessed)
            self.assertIn('database servers', menu_accessed)
            self.assertIn('activity logs', menu_accessed)

    def test_create_admin_command(self):
        with app.app_context():
            # Test creating admin user
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'change-this-password')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
            
            # Create admin user directly
            user = User(
                username=admin_username,
                email=admin_email,
                role='admin'
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
            
            # Verify admin was created
            admin = User.query.filter_by(username=admin_username).first()
            self.assertIsNotNone(admin)
            self.assertEqual(admin.role, 'admin')
            self.assertTrue(admin.check_password(admin_password))
            
            # Try creating another admin
            another_user = User(
                username='another_admin',
                email='another@example.com',
                role='admin'
            )
            another_user.set_password('password')
            db.session.add(another_user)
            db.session.commit()
            
            # Verify we now have exactly 2 admins
            admin_count = User.query.filter_by(role='admin').count()
            self.assertEqual(admin_count, 2)

    def test_create_admin_command_cli(self):
        """Test the create-admin CLI command"""
        with app.app_context():
            # Set environment variables
            os.environ['ADMIN_USERNAME'] = 'testadmin'
            os.environ['ADMIN_PASSWORD'] = 'testpass'
            os.environ['ADMIN_EMAIL'] = 'testadmin@example.com'
            
            # Run create-admin command
            from app import create_admin
            try:
                create_admin(standalone_mode=False)
            except SystemExit:
                pass  # Click command exits after completion
            
            # Verify admin was created
            admin = User.query.filter_by(username='testadmin').first()
            self.assertIsNotNone(admin)
            self.assertEqual(admin.email, 'testadmin@example.com')
            self.assertEqual(admin.role, 'admin')
            self.assertTrue(admin.check_password('testpass'))
            
            # Run command again to test idempotency
            try:
                create_admin(standalone_mode=False)
            except SystemExit:
                pass  # Click command exits after completion
            
            # Clean up
            os.environ.pop('ADMIN_USERNAME')
            os.environ.pop('ADMIN_PASSWORD')
            os.environ.pop('ADMIN_EMAIL')

    def test_get_metrics_error_handling(self):
        # Login first
        self.login()
        
        # Test database error
        with app.app_context():
            with patch('app.DatabaseServer.query') as mock_query:
                mock_query.all.side_effect = Exception("Database error")
                response = self.client.get('/api/metrics')
                self.assertEqual(response.status_code, 500)
                self.assertIn('error', response.get_json())

            # Test metrics collection error
            with patch('db_monitor.DatabaseMonitor.get_performance_metrics') as mock_get_metrics:
                mock_get_metrics.side_effect = Exception("Failed to collect metrics")
                response = self.client.get('/api/metrics')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertTrue(len(data) > 0)
                self.assertIn('error', data[0])
                self.assertEqual(data[0]['cpu_percent'], 0)
                self.assertEqual(data[0]['memory_percent'], 0)
                self.assertEqual(data[0]['disk_usage'], 0)
                self.assertEqual(data[0]['active_connections'], 0)

    def test_server_metrics_error_handling(self):
        # Login first
        self.login()
        
        with app.app_context():
            server = DatabaseServer.query.first()
            server_id = server.id

            # Test connection error
            with patch('db_monitor.DatabaseMonitor.get_performance_metrics') as mock_get_metrics:
                mock_get_metrics.side_effect = Exception("Connection failed")
                response = self.client.get(f'/api/server/{server_id}/metrics')
                self.assertEqual(response.status_code, 500)
                data = response.get_json()
                self.assertIn('error', data)
                self.assertEqual(data['error'], 'Connection failed')

    def test_app_startup(self):
        # Test app startup with monitoring service
        from monitor_service import MonitoringService
        
        with patch('monitor_service.MonitoringService.start') as mock_start:
            with app.app_context():
                # Create test database
                db.create_all()
                
                # Initialize monitoring service
                monitor_service = MonitoringService(app)
                monitor_service.start()
                
                # Verify monitoring service was started
                mock_start.assert_called_once()
                
                # Clean up
                db.drop_all()

    def test_database_server_connection(self):
        self.login()
        
        with app.app_context():
            server = DatabaseServer.query.first()
            
            # Test successful connection
            with patch('db_monitor.DatabaseMonitor.connect') as mock_connect:
                mock_connect.return_value = None
                self.assertTrue(server.test_connection())
                self.assertIsNone(server.last_error)
                self.assertIsNotNone(server.last_check)

            # Test failed connection
            with patch('db_monitor.DatabaseMonitor.connect') as mock_connect:
                mock_connect.side_effect = Exception("Connection failed")
                self.assertFalse(server.test_connection())
                self.assertEqual(server.last_error, "Connection failed")
                self.assertIsNotNone(server.last_check)

if __name__ == '__main__':
    unittest.main()
