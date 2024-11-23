import psycopg2
import mysql.connector
import time
from datetime import datetime

class DatabaseMonitor:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.db_type = config['db_type']

    def connect(self):
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['username'],
                    password=self.config['password']
                )
            elif self.db_type == 'mysql':
                self.connection = mysql.connector.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['username'],
                    password=self.config['password']
                )
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()

    def get_performance_metrics(self):
        metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_usage': 0,
            'active_connections': 0,
            'timestamp': datetime.now().isoformat()
        }

        try:
            cursor = self.connection.cursor()
            
            if self.db_type == 'postgresql':
                # Get active connections
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                metrics['active_connections'] = cursor.fetchone()[0]

                # Get database size
                cursor.execute("SELECT pg_database_size(current_database())")
                metrics['disk_usage'] = cursor.fetchone()[0] / (1024 * 1024 * 1024)  # Convert to GB

                # Get CPU and memory usage (requires pg_stat_statements extension)
                cursor.execute("""
                    SELECT 
                        (SELECT value FROM pg_sysctl_settings WHERE name = 'kernel.sched_util_clamp_min')::float AS cpu_percent,
                        (SELECT sum(work_mem::bigint) FROM pg_settings WHERE name = 'work_mem')::float 
                        / (SELECT setting::bigint FROM pg_settings WHERE name = 'shared_buffers')::float * 100 AS memory_percent
                """)
                row = cursor.fetchone()
                if row:
                    metrics['cpu_percent'] = row[0] if row[0] else 0
                    metrics['memory_percent'] = row[1] if row[1] else 0

            elif self.db_type == 'mysql':
                # Get active connections
                cursor.execute("SELECT COUNT(*) FROM information_schema.processlist WHERE command != 'Sleep'")
                metrics['active_connections'] = cursor.fetchone()[0]

                # Get database size
                cursor.execute("SELECT SUM(data_length + index_length) / 1024 / 1024 / 1024 FROM information_schema.tables")
                metrics['disk_usage'] = cursor.fetchone()[0] or 0

                # Get CPU and memory usage (requires performance_schema)
                cursor.execute("""
                    SELECT 
                        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'CPU_UTILIZATION') AS cpu_percent,
                        (SELECT ROUND((VARIABLE_VALUE/1024/1024), 2) FROM performance_schema.global_status WHERE VARIABLE_NAME = 'MEMORY_USED') AS memory_used
                """)
                row = cursor.fetchone()
                if row:
                    metrics['cpu_percent'] = float(row[0]) if row[0] else 0
                    metrics['memory_percent'] = float(row[1]) if row[1] else 0

            cursor.close()
        except Exception as e:
            print(f"Error getting performance metrics: {str(e)}")

        return metrics

    def get_active_queries(self):
        queries = []
        try:
            cursor = self.connection.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        pid,
                        usename as username,
                        datname as database,
                        query,
                        EXTRACT(EPOCH FROM (now() - query_start)) as duration,
                        state
                    FROM pg_stat_activity 
                    WHERE state != 'idle' 
                    AND query NOT ILIKE '%pg_stat_activity%'
                    ORDER BY duration DESC
                """)
            elif self.db_type == 'mysql':
                cursor.execute("""
                    SELECT 
                        ID as pid,
                        USER as username,
                        DB as database,
                        INFO as query,
                        TIME as duration,
                        STATE as state
                    FROM information_schema.processlist
                    WHERE COMMAND != 'Sleep'
                    AND INFO IS NOT NULL
                    ORDER BY TIME DESC
                """)

            for row in cursor.fetchall():
                queries.append({
                    'pid': str(row[0]),
                    'username': row[1],
                    'database': row[2],
                    'query': row[3],
                    'duration': float(row[4]) if row[4] else 0,
                    'state': row[5]
                })

            cursor.close()
        except Exception as e:
            print(f"Error getting active queries: {str(e)}")

        return queries

    def get_query_history(self):
        queries = []
        try:
            cursor = self.connection.cursor()
            
            if self.db_type == 'postgresql':
                # Requires pg_stat_statements extension
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time / 1000 as total_duration_sec,
                        mean_exec_time / 1000 as avg_duration_sec,
                        rows
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY total_exec_time DESC
                    LIMIT 1000
                """)
            elif self.db_type == 'mysql':
                # Requires performance_schema
                cursor.execute("""
                    SELECT 
                        DIGEST_TEXT as query,
                        COUNT_STAR as calls,
                        SUM_TIMER_WAIT/1000000000000 as total_duration_sec,
                        AVG_TIMER_WAIT/1000000000000 as avg_duration_sec,
                        SUM_ROWS_AFFECTED as rows
                    FROM performance_schema.events_statements_summary_by_digest
                    WHERE DIGEST_TEXT IS NOT NULL
                    ORDER BY SUM_TIMER_WAIT DESC
                    LIMIT 1000
                """)

            for row in cursor.fetchall():
                queries.append({
                    'query': row[0],
                    'calls': row[1],
                    'total_duration': row[2],
                    'avg_duration': row[3],
                    'rows_affected': row[4]
                })

            cursor.close()
        except Exception as e:
            print(f"Error getting query history: {str(e)}")

        return queries
