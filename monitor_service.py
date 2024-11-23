from db_monitor import DatabaseMonitor
from app import DatabaseServer, db
import threading
import time
from datetime import datetime
import json
from prometheus_client import start_http_server, Gauge

# Prometheus metrics
db_active_connections = Gauge('db_active_connections', 'Number of active database connections', ['db_name', 'db_type'])
db_size = Gauge('db_size_mb', 'Database size in MB', ['db_name', 'db_type'])
db_cpu_usage = Gauge('db_cpu_usage', 'Database CPU usage percentage', ['db_name', 'db_type'])
db_memory_usage = Gauge('db_memory_usage', 'Database memory usage percentage', ['db_name', 'db_type'])
db_disk_usage = Gauge('db_disk_usage', 'Database disk usage percentage', ['db_name', 'db_type'])
db_cache_hit_ratio = Gauge('db_cache_hit_ratio', 'Database cache hit ratio', ['db_name', 'db_type'])
db_transaction_rate = Gauge('db_transaction_rate', 'Database transaction rate', ['db_name', 'db_type'])

class MonitoringService:
    def __init__(self, app, interval=60):
        self.app = app
        self.interval = interval
        self.monitors = {}
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the monitoring service"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Start Prometheus metrics server
        start_http_server(9090)
        
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            with self.app.app_context():
                try:
                    self._collect_metrics()
                except Exception as e:
                    print(f"Error collecting metrics: {str(e)}")
            time.sleep(self.interval)
            
    def _collect_metrics(self):
        """Collect metrics from all registered database servers"""
        servers = DatabaseServer.query.all()
        
        for server in servers:
            try:
                # Create monitor if it doesn't exist
                if server.id not in self.monitors:
                    config = {
                        'db_type': server.db_type,
                        'host': server.host,
                        'port': server.port,
                        'database': 'postgres' if server.db_type == 'postgresql' else 'master',  # Default databases
                        'username': server.username,
                        'password': server.password
                    }
                    self.monitors[server.id] = DatabaseMonitor(config)
                
                monitor = self.monitors[server.id]
                
                # Connect if not connected
                if not monitor.connection:
                    monitor.connect()
                
                # Collect metrics
                metrics = monitor.get_performance_metrics()
                
                # Update Prometheus metrics
                labels = {'db_name': server.name, 'db_type': server.db_type}
                
                db_active_connections.labels(**labels).set(metrics['active_connections'])
                db_size.labels(**labels).set(metrics['database_size_mb'])
                db_cpu_usage.labels(**labels).set(metrics['cpu_percent'])
                db_memory_usage.labels(**labels).set(metrics['memory_percent'])
                db_disk_usage.labels(**labels).set(metrics['disk_usage'])
                
                if 'cache_hit_ratio' in metrics:
                    db_cache_hit_ratio.labels(**labels).set(metrics['cache_hit_ratio'])
                if 'transaction_rate' in metrics:
                    db_transaction_rate.labels(**labels).set(metrics['transaction_rate'])
                
            except Exception as e:
                print(f"Error monitoring server {server.name}: {str(e)}")
                if server.id in self.monitors:
                    try:
                        self.monitors[server.id].close()
                    except:
                        pass
                    del self.monitors[server.id]
