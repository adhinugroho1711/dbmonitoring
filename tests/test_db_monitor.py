import unittest
from db_monitor import DatabaseMonitor
from unittest.mock import patch, MagicMock

class TestDatabaseMonitor(unittest.TestCase):
    def setUp(self):
        self.postgres_config = {
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        }
        
        self.mysql_config = {
            'db_type': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        }

    @patch('psycopg2.connect')
    def test_postgres_connection(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Test connection
        monitor = DatabaseMonitor(self.postgres_config)
        monitor.connect()
        
        # Verify connection was attempted with correct parameters
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            database='test_db',
            user='test_user',
            password='test_pass'
        )

    @patch('mysql.connector.connect')
    def test_mysql_connection(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Test connection
        monitor = DatabaseMonitor(self.mysql_config)
        monitor.connect()
        
        # Verify connection was attempted with correct parameters
        mock_connect.assert_called_once_with(
            host='localhost',
            port=3306,
            database='test_db',
            user='test_user',
            password='test_pass'
        )

    @patch('psycopg2.connect')
    def test_get_performance_metrics_postgres(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Setup cursor mock to return test data
        mock_cursor.fetchone.return_value = [5]  # Active connections
        
        # Create monitor and connect
        monitor = DatabaseMonitor(self.postgres_config)
        monitor.connect()
        
        # Get metrics
        metrics = monitor.get_performance_metrics()
        
        # Verify metrics structure
        self.assertIsInstance(metrics, dict)
        self.assertIn('active_connections', metrics)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)

    def test_connection_error(self):
        # Test with invalid config
        invalid_config = {
            'db_type': 'postgresql',
            'host': 'invalid_host',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        }
        
        monitor = DatabaseMonitor(invalid_config)
        with self.assertRaises(ConnectionError):
            monitor.connect()

    @patch('psycopg2.connect')
    def test_get_active_queries_postgres(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock cursor description and fetchall results
        mock_cursor.description = [
            ('pid',), ('usename',), ('query',), ('state',), ('duration_seconds',)
        ]
        mock_cursor.fetchall.return_value = [
            (1, 'user1', 'SELECT * FROM table1', 'active', 10),
            (2, 'user2', 'UPDATE table2', 'idle in transaction', 5)
        ]
        
        # Create monitor and connect
        monitor = DatabaseMonitor(self.postgres_config)
        monitor.connect()
        
        # Get active queries
        queries = monitor.get_active_queries()
        
        # Verify results
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[0]['pid'], 1)
        self.assertEqual(queries[0]['query'], 'SELECT * FROM table1')
        self.assertEqual(queries[1]['usename'], 'user2')

    @patch('mysql.connector.connect')
    def test_get_active_queries_mysql(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock cursor description and fetchall results
        mock_cursor.description = [
            ('ID',), ('USER',), ('query',), ('STATE',), ('duration_seconds',)
        ]
        mock_cursor.fetchall.return_value = [
            (1, 'user1', 'SELECT * FROM table1', 'executing', 10),
            (2, 'user2', 'UPDATE table2', 'sending data', 5)
        ]
        
        # Create monitor and connect
        monitor = DatabaseMonitor(self.mysql_config)
        monitor.connect()
        
        # Get active queries
        queries = monitor.get_active_queries()
        
        # Verify results
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[0]['ID'], 1)
        self.assertEqual(queries[0]['query'], 'SELECT * FROM table1')
        self.assertEqual(queries[1]['USER'], 'user2')

    @patch('mysql.connector.connect')
    def test_get_database_size_mysql(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock fetchone result
        mock_cursor.fetchone.return_value = [1024.5]  # 1024.5 MB
        
        # Create monitor and connect
        monitor = DatabaseMonitor(self.mysql_config)
        monitor.connect()
        
        # Get database size
        size = monitor.get_database_size()
        
        # Verify size
        self.assertEqual(size, 1024.5)

    @patch('mysql.connector.connect')
    def test_get_performance_metrics_mysql(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock fetchall results for buffer pool stats
        mock_cursor.fetchall.return_value = [
            ('Innodb_buffer_pool_reads', '1000'),
            ('Innodb_buffer_pool_read_requests', '10000')
        ]
        
        # Create monitor and connect
        monitor = DatabaseMonitor(self.mysql_config)
        monitor.connect()
        
        # Get metrics
        metrics = monitor.get_performance_metrics()
        
        # Verify metrics
        self.assertIn('buffer_pool_hit_ratio', metrics)
        self.assertEqual(metrics['buffer_pool_hit_ratio'], 90.0)  # (10000-1000)/10000 * 100

    def test_error_handling(self):
        # Test error handling in get_active_connections
        monitor = DatabaseMonitor(self.postgres_config)
        self.assertEqual(monitor.get_active_connections(), -1)
        
        # Test error handling in get_database_size
        self.assertEqual(monitor.get_database_size(), -1)
        
        # Test error handling in get_active_queries
        self.assertEqual(monitor.get_active_queries(), [])

    def test_close_connection(self):
        # Setup mock connection
        mock_conn = MagicMock()
        
        # Create monitor and set connection
        monitor = DatabaseMonitor(self.postgres_config)
        monitor.connection = mock_conn
        
        # Close connection
        monitor.close()
        
        # Verify close was called
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
