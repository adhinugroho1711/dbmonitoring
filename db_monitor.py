import psycopg2
import mysql.connector
import psutil
import json
from datetime import datetime
from typing import Dict, Any, List

class DatabaseMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.db_type = config['db_type']

    def connect(self) -> None:
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['username'],
                    password=self.config['password']
                )
            elif self.db_type in ['mysql', 'mariadb']:
                self.connection = mysql.connector.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['username'],
                    password=self.config['password']
                )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.db_type}: {str(e)}")

    def get_active_connections(self) -> int:
        queries = {
            'postgresql': """
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active'
            """,
            'mysql': """
                SELECT COUNT(*) FROM information_schema.processlist 
                WHERE command != 'Sleep'
            """,
            'mariadb': """
                SELECT COUNT(*) FROM information_schema.processlist 
                WHERE command != 'Sleep'
            """
        }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(queries[self.db_type])
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            return -1

    def get_database_size(self) -> float:
        queries = {
            'postgresql': """
                SELECT pg_database_size(current_database())/1024/1024 as size_mb
            """,
            'mysql': """
                SELECT SUM(data_length + index_length) / 1024 / 1024
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
            """,
            'mariadb': """
                SELECT SUM(data_length + index_length) / 1024 / 1024
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
            """
        }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(queries[self.db_type])
            size = cursor.fetchone()[0]
            cursor.close()
            return float(size)
        except Exception as e:
            return -1

    def get_performance_metrics(self) -> Dict[str, Any]:
        metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'active_connections': self.get_active_connections(),
            'database_size_mb': self.get_database_size(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Get database-specific metrics
        if self.db_type == 'postgresql':
            cursor = self.connection.cursor()
            
            # Cache hit ratio
            cursor.execute("""
                SELECT 
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                FROM pg_statio_user_tables
            """)
            metrics['cache_hit_ratio'] = cursor.fetchone()[0]
            
            # Transaction rate
            cursor.execute("""
                SELECT xact_commit + xact_rollback 
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            metrics['transaction_rate'] = cursor.fetchone()[0]
            
            cursor.close()
            
        elif self.db_type in ['mysql', 'mariadb']:
            cursor = self.connection.cursor()
            
            # Buffer pool hit ratio
            cursor.execute("""
                SHOW GLOBAL STATUS 
                WHERE Variable_name IN ('Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests')
            """)
            results = dict(cursor.fetchall())
            reads = float(results['Innodb_buffer_pool_reads'])
            requests = float(results['Innodb_buffer_pool_read_requests'])
            metrics['buffer_pool_hit_ratio'] = ((requests - reads) / requests) * 100 if requests > 0 else 0
            
            cursor.close()

        return metrics

    def get_active_queries(self) -> List[Dict[str, Any]]:
        queries = {
            'postgresql': """
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr as ip_address,
                    datname as database_name,
                    query,
                    state,
                    query_start as access_time,
                    EXTRACT(EPOCH FROM now() - query_start)::INT as duration_seconds,
                    CASE 
                        WHEN EXTRACT(EPOCH FROM now() - query_start) >= 3600 THEN 
                            ROUND(EXTRACT(EPOCH FROM now() - query_start)/3600) || ' hours'
                        WHEN EXTRACT(EPOCH FROM now() - query_start) >= 60 THEN 
                            ROUND(EXTRACT(EPOCH FROM now() - query_start)/60) || ' minutes'
                        ELSE 
                            ROUND(EXTRACT(EPOCH FROM now() - query_start)) || ' seconds'
                    END as duration_text
                FROM pg_stat_activity 
                WHERE state NOT IN ('idle', 'idle in transaction')
                  AND query != '<IDLE>'
                  AND query NOT ILIKE '%pg_stat_activity%'
                ORDER BY duration_seconds DESC
            """,
            'mysql': """
                SELECT 
                    ID,
                    USER,
                    HOST as ip_address,
                    DB as database_name,
                    COMMAND as application_name,
                    INFO as query,
                    STATE,
                    TIME_MS/1000 as duration_seconds,
                    CASE 
                        WHEN TIME_MS/1000 >= 3600 THEN 
                            CONCAT(ROUND(TIME_MS/1000/3600), ' hours')
                        WHEN TIME_MS/1000 >= 60 THEN 
                            CONCAT(ROUND(TIME_MS/1000/60), ' minutes')
                        ELSE 
                            CONCAT(ROUND(TIME_MS/1000), ' seconds')
                    END as duration_text,
                    TIME as access_time
                FROM information_schema.processlist
                WHERE command != 'Sleep'
                  AND INFO IS NOT NULL
                ORDER BY TIME DESC
            """,
            'mariadb': """
                SELECT 
                    ID,
                    USER,
                    HOST as ip_address,
                    DB as database_name,
                    COMMAND as application_name,
                    INFO as query,
                    STATE,
                    TIME as duration_seconds,
                    CASE 
                        WHEN TIME >= 3600 THEN 
                            CONCAT(ROUND(TIME/3600), ' hours')
                        WHEN TIME >= 60 THEN 
                            CONCAT(ROUND(TIME/60), ' minutes')
                        ELSE 
                            CONCAT(TIME, ' seconds')
                    END as duration_text,
                    NOW() - INTERVAL TIME SECOND as access_time
                FROM information_schema.processlist
                WHERE command != 'Sleep'
                  AND INFO IS NOT NULL
                ORDER BY TIME DESC
            """
        }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(queries[self.db_type])
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Convert access_time to string if it's a datetime object
                if isinstance(result.get('access_time'), datetime):
                    result['access_time'] = result['access_time'].isoformat()
                # Extract IP from HOST for MySQL/MariaDB (format: ip:port)
                if self.db_type in ['mysql', 'mariadb'] and 'ip_address' in result:
                    result['ip_address'] = result['ip_address'].split(':')[0]
                results.append(result)
            cursor.close()
            return results
        except Exception as e:
            print(f"Error getting active queries: {str(e)}")
            return []

    def close(self) -> None:
        if self.connection:
            self.connection.close()
