"""
SQLite database storage for dynamometer data persistence.
Handles long-term data storage and retrieval for historical analysis.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import threading
from typing import List, Dict, Optional, Tuple


class DataStorage:
    """Handles persistent storage of dynamometer data using SQLite."""
    
    def __init__(self, db_path: str = "dyno_data.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create main data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dyno_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    relative_time REAL NOT NULL,
                    drive_rpm INTEGER,
                    drive_current REAL,
                    drive_voltage REAL,
                    drive_temp_fet REAL,
                    drive_temp_motor REAL,
                    brake_rpm INTEGER,
                    brake_current REAL,
                    brake_voltage REAL,
                    brake_temp_fet REAL,
                    brake_temp_motor REAL,
                    mechanical_power REAL,
                    session_start REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for efficient time-based queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_time 
                ON dyno_data(session_start, relative_time)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON dyno_data(created_at)
            ''')
            
            conn.commit()
    
    def store_data_point(self, timestamp: float, relative_time: float, 
                        drive_data: Dict, brake_data: Dict, dyno_data: Dict,
                        session_start: float):
        """Store a single data point to the database."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO dyno_data (
                            timestamp, relative_time, drive_rpm, drive_current, 
                            drive_voltage, drive_temp_fet, drive_temp_motor,
                            brake_rpm, brake_current, brake_voltage, 
                            brake_temp_fet, brake_temp_motor, mechanical_power,
                            session_start
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp, relative_time,
                        drive_data.get('rpm', 0), drive_data.get('current', 0.0),
                        drive_data.get('voltage', 0.0), drive_data.get('temp_fet', 0.0),
                        drive_data.get('temp_motor', 0.0),
                        brake_data.get('rpm', 0), brake_data.get('current', 0.0),
                        brake_data.get('voltage', 0.0), brake_data.get('temp_fet', 0.0),
                        brake_data.get('temp_motor', 0.0),
                        dyno_data.get('drive_power', 0.0) + dyno_data.get('brake_power', 0.0),
                        session_start
                    ))
                    
                    conn.commit()
            except sqlite3.Error as e:
                print(f"Database error storing data: {e}")
    
    def get_data_for_timerange(self, session_start: float, 
                              time_range_seconds: Optional[float] = None) -> Dict[str, List]:
        """
        Get data for a specific time range from the current session.
        
        Args:
            session_start: Session start timestamp
            time_range_seconds: How many seconds back to retrieve (None for all)
        
        Returns:
            Dictionary with lists of data points
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    if time_range_seconds is None:
                        # Get all data for this session
                        cursor.execute('''
                            SELECT relative_time, drive_rpm, drive_current, drive_voltage,
                                   drive_temp_fet, drive_temp_motor, brake_rpm, brake_current,
                                   brake_voltage, brake_temp_fet, brake_temp_motor, mechanical_power
                            FROM dyno_data 
                            WHERE session_start = ?
                            ORDER BY relative_time
                        ''', (session_start,))
                    else:
                        # Get data for specific time range (last N seconds)
                        cursor.execute('''
                            SELECT relative_time, drive_rpm, drive_current, drive_voltage,
                                   drive_temp_fet, drive_temp_motor, brake_rpm, brake_current,
                                   brake_voltage, brake_temp_fet, brake_temp_motor, mechanical_power
                            FROM dyno_data 
                            WHERE session_start = ?
                            ORDER BY relative_time DESC
                            LIMIT ?
                        ''', (session_start, int(time_range_seconds * 10)))  # Assuming 10Hz data
                    
                    rows = cursor.fetchall()
                    
                    # If we limited by time range, reverse to get chronological order
                    if time_range_seconds is not None:
                        rows = list(reversed(rows))
                    
                    # Convert to the expected format
                    if not rows:
                        return self._empty_data_dict()
                    
                    data = {
                        'timestamps': [row[0] for row in rows],
                        'drive_rpm': [row[1] for row in rows],
                        'drive_current': [row[2] for row in rows],
                        'drive_voltage': [row[3] for row in rows],
                        'drive_temp_fet': [row[4] for row in rows],
                        'drive_temp_motor': [row[5] for row in rows],
                        'brake_rpm': [row[6] for row in rows],
                        'brake_current': [row[7] for row in rows],
                        'brake_voltage': [row[8] for row in rows],
                        'brake_temp_fet': [row[9] for row in rows],
                        'brake_temp_motor': [row[10] for row in rows],
                        'drive_power': [row[11] / 2 for row in rows],  # Split stored power equally for now
                        'brake_power': [row[11] / 2 for row in rows]
                    }
                    
                    return data
                    
            except sqlite3.Error as e:
                print(f"Database error retrieving data: {e}")
                return self._empty_data_dict()
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """Remove data older than specified days."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cutoff_time = datetime.now() - timedelta(days=days_to_keep)
                    
                    cursor.execute('''
                        DELETE FROM dyno_data 
                        WHERE created_at < ?
                    ''', (cutoff_time,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        print(f"Cleaned up {deleted_count} old data points")
                        
            except sqlite3.Error as e:
                print(f"Database error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the database."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT COUNT(*) FROM dyno_data')
                    total_records = cursor.fetchone()[0]
                    
                    cursor.execute('''
                        SELECT COUNT(DISTINCT session_start) FROM dyno_data
                    ''')
                    total_sessions = cursor.fetchone()[0]
                    
                    # Get database file size
                    db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                    
                    return {
                        'total_records': total_records,
                        'total_sessions': total_sessions,
                        'db_size_bytes': db_size
                    }
                    
            except sqlite3.Error as e:
                print(f"Database error getting stats: {e}")
                return {'total_records': 0, 'total_sessions': 0, 'db_size_bytes': 0}
    
    def clear_session_data(self, session_start: float):
        """Clear all data for a specific session (used on ESP32 restart)."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        DELETE FROM dyno_data WHERE session_start = ?
                    ''', (session_start,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        print(f"Cleared {deleted_count} data points from restarted session")
                        
            except sqlite3.Error as e:
                print(f"Database error clearing session data: {e}")
    
    def _empty_data_dict(self) -> Dict[str, List]:
        """Return empty data dictionary with correct structure."""
        return {
            'timestamps': [],
            'drive_rpm': [],
            'drive_current': [],
            'drive_voltage': [],
            'drive_temp_fet': [],
            'drive_temp_motor': [],
            'brake_rpm': [],
            'brake_current': [],
            'brake_voltage': [],
            'brake_temp_fet': [],
            'brake_temp_motor': [],
            'drive_power': [],
            'brake_power': []
        }
    
    def close(self):
        """Close database connection."""
        pass  # SQLite connections are closed automatically with context managers