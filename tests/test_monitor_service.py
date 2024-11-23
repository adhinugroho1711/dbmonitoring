import pytest
from unittest.mock import Mock, patch
from contextlib import ExitStack
from monitor_service import MonitoringService
from app import app as flask_app, DatabaseServer, db
import threading
import time

@pytest.fixture
def app():
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def mock_db_monitor():
    with patch('monitor_service.DatabaseMonitor') as mock:
        monitor = Mock()
        monitor.connection = None
        monitor.get_performance_metrics.return_value = {
            'active_connections': 10,
            'database_size_mb': 1000,
            'cpu_percent': 25.5,
            'memory_percent': 60.2,
            'disk_usage': 45.8,
            'cache_hit_ratio': 95.5,
            'transaction_rate': 100.0
        }
        mock.return_value = monitor
        yield mock

@pytest.fixture
def mock_prometheus():
    # Create a mock for the labeled gauge
    labeled_gauge = Mock()
    labeled_gauge.set = Mock()
    
    # Create a mock for the gauge itself
    gauge = Mock()
    gauge.labels.return_value = labeled_gauge
    
    patches = [
        patch('monitor_service.start_http_server'),
        patch('monitor_service.db_active_connections', gauge),
        patch('monitor_service.db_size', gauge),
        patch('monitor_service.db_cpu_usage', gauge),
        patch('monitor_service.db_memory_usage', gauge),
        patch('monitor_service.db_disk_usage', gauge),
        patch('monitor_service.db_cache_hit_ratio', gauge),
        patch('monitor_service.db_transaction_rate', gauge)
    ]
    
    with ExitStack() as stack:
        mocks = [stack.enter_context(p) for p in patches]
        yield mocks[0], labeled_gauge

@pytest.fixture
def test_server(app):
    with app.app_context():
        server = DatabaseServer(
            name='test_server',
            db_type='postgresql',
            host='localhost',
            port=5432,
            username='test',
            password='test'
        )
        db.session.add(server)
        db.session.commit()
        yield server
        db.session.delete(server)
        db.session.commit()

def test_monitoring_service_lifecycle(mock_prometheus):
    """Test starting and stopping the monitoring service"""
    service = MonitoringService(flask_app, interval=1)
    
    assert not service.running
    assert service.thread is None
    
    service.start()
    assert service.running
    assert isinstance(service.thread, threading.Thread)
    assert service.thread.daemon
    
    service.stop()
    assert not service.running
    
    mock_server, _ = mock_prometheus
    mock_server.assert_called_once_with(9090)

def test_metrics_collection(mock_db_monitor, mock_prometheus, test_server):
    """Test collecting metrics from a database server"""
    service = MonitoringService(flask_app, interval=1)
    
    # Start service and wait for a short time
    service.start()
    time.sleep(0.1)  # Just enough time for one cycle
    service.stop()
    
    # Verify DatabaseMonitor was created and used
    mock_db_monitor.assert_called_once()
    monitor = mock_db_monitor.return_value
    monitor.connect.assert_called()  # Allow multiple calls
    monitor.get_performance_metrics.assert_called()
    
    # Verify Prometheus metrics were updated
    _, labeled_gauge = mock_prometheus
    
    # Verify that metrics were set
    assert labeled_gauge.set.called

def test_error_handling(mock_db_monitor, mock_prometheus, test_server):
    """Test error handling during metrics collection"""
    service = MonitoringService(flask_app, interval=1)
    
    # Make the monitor raise an exception
    monitor = mock_db_monitor.return_value
    monitor.get_performance_metrics.side_effect = Exception("Test error")
    
    # Start service and wait for a short time
    service.start()
    time.sleep(0.1)  # Just enough time for one cycle
    service.stop()
    
    # Verify monitor was created and error was handled
    mock_db_monitor.assert_called_once()
    monitor.connect.assert_called()  # Allow multiple calls
    monitor.get_performance_metrics.assert_called()
    monitor.close.assert_called()
    
    # The monitor should have been removed from service.monitors
    assert len(service.monitors) == 0

def test_multiple_servers(mock_db_monitor, mock_prometheus, test_server):
    """Test monitoring multiple servers"""
    # Add another test server
    with flask_app.app_context():
        server2 = DatabaseServer(
            name='test_server2',
            db_type='mysql',
            host='localhost',
            port=3306,
            username='test',
            password='test'
        )
        db.session.add(server2)
        db.session.commit()
    
    service = MonitoringService(flask_app, interval=1)
    
    # Start service and wait for one collection cycle
    service.start()
    time.sleep(1.5)
    service.stop()
    
    # Verify DatabaseMonitor was created for both servers
    assert mock_db_monitor.call_count == 2
    
    # Clean up
    with flask_app.app_context():
        db.session.delete(server2)
        db.session.commit()
