import sqlite3
from datetime import datetime
import statistics
import threading

class SensorDB:
    def __init__(self, db_path="sensor_data.db"):
        self.db_path = db_path
        self.db_lock = threading.Lock()  # 多线程锁
        self._init_db()

    # ---------------- 数据库连接 ----------------
    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)

    # ---------------- 初始化表 ----------------
    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                unit TEXT,
                UNIQUE(category_id, name),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                value REAL,
                FOREIGN KEY(sensor_id) REFERENCES sensors(id)
            )
            """)
            conn.commit()

    # ---------------- 内部工具函数 ----------------
    def _get_or_create_category(self, name, conn):
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        cursor.execute("SELECT id FROM categories WHERE name=?", (name,))
        return cursor.fetchone()[0]

    def _get_or_create_sensor(self, category_id, name, unit, conn):
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO sensors (category_id, name, unit) VALUES (?, ?, ?)", 
                       (category_id, name, unit))
        conn.commit()
        cursor.execute("SELECT id FROM sensors WHERE category_id=? AND name=?", (category_id, name))
        return cursor.fetchone()[0]

    # ---------------- 数据插入 ----------------
    def insert_data(self, data_dict):
        with self.db_lock:
            with self._connect() as conn:
                cursor = conn.cursor()
                for category_name, sensors in data_dict.items():
                    category_id = self._get_or_create_category(category_name, conn)
                    for sensor in sensors:
                        sensor_id = self._get_or_create_sensor(category_id, sensor['name'], sensor['unit'], conn)
                        cursor.execute("INSERT INTO sensor_data (sensor_id, value) VALUES (?, ?)", 
                                       (sensor_id, sensor['value']))
                conn.commit()

    # ---------------- 查询最新数据 ----------------
    def query_latest(self, category=None, sensor_name=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            sql = """
            SELECT c.name as category, s.name, s.unit, d.value, d.timestamp
            FROM sensor_data d
            JOIN sensors s ON d.sensor_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE d.id IN (SELECT MAX(id) FROM sensor_data GROUP BY sensor_id)
            """
            params = []
            if category:
                sql += " AND c.name=?"
                params.append(category)
            if sensor_name:
                sql += " AND s.name=?"
                params.append(sensor_name)
            cursor.execute(sql, params)
            return cursor.fetchall()

    # ---------------- 时间段查询原始数据 ----------------
    def query_by_time(self, start, end, category=None, sensor_name=None):
        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d %H:%M:%S")

        result = {}
        with self._connect() as conn:
            cursor = conn.cursor()
            sql = """
            SELECT c.name as category, s.name, s.unit, d.value, d.timestamp
            FROM sensor_data d
            JOIN sensors s ON d.sensor_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE d.timestamp BETWEEN ? AND ?
            """
            params = [start, end]
            if category:
                sql += " AND c.name=?"
                params.append(category)
            if sensor_name:
                sql += " AND s.name=?"
                params.append(sensor_name)
            sql += " ORDER BY d.timestamp"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            for cat, sensor, unit, value, ts in rows:
                result.setdefault(cat, {}).setdefault(sensor, []).append((ts, value))
        return result

    # ---------------- 时间段统计 ----------------
    def stats_by_time(self, start, end, category=None, sensor_name=None, agg=None):
        if agg is None:
            agg = ['count','min','max','avg','sum','median','stddev','variance','first','last']

        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d %H:%M:%S")

        result = {}
        with self._connect() as conn:
            cursor = conn.cursor()
            sql = """
            SELECT c.name as category, s.name, d.value
            FROM sensor_data d
            JOIN sensors s ON d.sensor_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE d.timestamp BETWEEN ? AND ?
            """
            params = [start, end]
            if category:
                sql += " AND c.name=?"
                params.append(category)
            if sensor_name:
                sql += " AND s.name=?"
                params.append(sensor_name)
            sql += " ORDER BY d.timestamp"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        data_dict = {}
        for cat, sensor, value in rows:
            data_dict.setdefault(cat, {}).setdefault(sensor, []).append(value)

        for cat, sensors in data_dict.items():
            for sensor, values in sensors.items():
                stats = {}
                if 'count' in agg: stats['count'] = len(values)
                if 'min' in agg: stats['min'] = min(values)
                if 'max' in agg: stats['max'] = max(values)
                if 'sum' in agg: stats['sum'] = sum(values)
                if 'avg' in agg: stats['avg'] = sum(values)/len(values) if values else None
                if 'median' in agg: stats['median'] = statistics.median(values) if values else None
                if 'variance' in agg: stats['variance'] = statistics.variance(values) if len(values)>1 else 0
                if 'stddev' in agg: stats['stddev'] = statistics.stdev(values) if len(values)>1 else 0
                if 'first' in agg: stats['first'] = values[0] if values else None
                if 'last' in agg: stats['last'] = values[-1] if values else None
                result.setdefault(cat, {})[sensor] = stats
        return result