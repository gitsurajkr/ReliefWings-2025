#!/usr/bin/env python3
"""
Database Module for ReliefWings Drone Telemetry System
Handles SQLite database operations for offline telemetry buffering
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

class TelemetryDatabase:
    """SQLite database manager for offline telemetry buffering"""
    
    def __init__(self, db_path: str = "/tmp/drone_telemetry.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create telemetry table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drone_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    seq_number INTEGER NOT NULL,
                    data TEXT NOT NULL,  -- JSON string of telemetry data
                    sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drone_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    args TEXT,  -- JSON string of command arguments
                    status TEXT DEFAULT 'pending',
                    result TEXT,  -- JSON string of command result
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                )
            ''')
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drone_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,  -- JSON string of additional data
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_drone_id ON telemetry(drone_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_sent ON telemetry(sent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_drone_id ON commands(drone_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_drone_id ON logs(drone_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_telemetry(self, drone_id: str, telemetry_data: Dict[str, Any], seq_number: int) -> bool:
        """Store telemetry data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO telemetry (drone_id, timestamp, seq_number, data)
                VALUES (?, ?, ?, ?)
            ''', (
                drone_id,
                telemetry_data.get('ts', 0),
                seq_number,
                json.dumps(telemetry_data)
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Stored telemetry for drone {drone_id}, seq {seq_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store telemetry: {e}")
            return False
    
    def get_unsent_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unsent telemetry data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, drone_id, timestamp, seq_number, data
                FROM telemetry
                WHERE sent = 0
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            telemetry_list = []
            for row in rows:
                telemetry_list.append({
                    'id': row[0],
                    'drone_id': row[1],
                    'timestamp': row[2],
                    'seq_number': row[3],
                    'data': json.loads(row[4])
                })
            
            logger.debug(f"Retrieved {len(telemetry_list)} unsent telemetry records")
            return telemetry_list
            
        except Exception as e:
            logger.error(f"Failed to get unsent telemetry: {e}")
            return []
    
    def mark_telemetry_sent(self, telemetry_ids: List[int]) -> bool:
        """Mark telemetry records as sent"""
        try:
            if not telemetry_ids:
                return True
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(telemetry_ids))
            cursor.execute(f'''
                UPDATE telemetry
                SET sent = 1
                WHERE id IN ({placeholders})
            ''', telemetry_ids)
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Marked {len(telemetry_ids)} telemetry records as sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark telemetry as sent: {e}")
            return False
    
    def store_command(self, drone_id: str, command: str, args: Dict[str, Any] = None) -> int:
        """Store received command in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO commands (drone_id, command, args)
                VALUES (?, ?, ?)
            ''', (
                drone_id,
                command,
                json.dumps(args) if args else None
            ))
            
            command_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Stored command {command} for drone {drone_id} with ID {command_id}")
            return command_id
            
        except Exception as e:
            logger.error(f"Failed to store command: {e}")
            return -1
    
    def update_command_status(self, command_id: int, status: str, result: Any = None) -> bool:
        """Update command execution status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE commands
                SET status = ?, result = ?, executed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                status,
                json.dumps(result) if result else None,
                command_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Updated command {command_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update command status: {e}")
            return False
    
    def get_pending_commands(self, drone_id: str) -> List[Dict[str, Any]]:
        """Get pending commands for a drone"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, command, args, received_at
                FROM commands
                WHERE drone_id = ? AND status = 'pending'
                ORDER BY received_at ASC
            ''', (drone_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            commands = []
            for row in rows:
                commands.append({
                    'id': row[0],
                    'command': row[1],
                    'args': json.loads(row[2]) if row[2] else None,
                    'received_at': row[3]
                })
            
            logger.debug(f"Retrieved {len(commands)} pending commands for drone {drone_id}")
            return commands
            
        except Exception as e:
            logger.error(f"Failed to get pending commands: {e}")
            return []
    
    def log_event(self, drone_id: str, level: str, message: str, data: Dict[str, Any] = None) -> bool:
        """Log an event to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (drone_id, level, message, data)
                VALUES (?, ?, ?, ?)
            ''', (
                drone_id,
                level,
                message,
                json.dumps(data) if data else None
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 7) -> bool:
        """Clean up old telemetry and log data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old sent telemetry
            cursor.execute('''
                DELETE FROM telemetry
                WHERE sent = 1 AND created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            telemetry_deleted = cursor.rowcount
            
            # Clean up old logs
            cursor.execute('''
                DELETE FROM logs
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            logs_deleted = cursor.rowcount
            
            # Clean up old completed commands
            cursor.execute('''
                DELETE FROM commands
                WHERE status != 'pending' AND executed_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            commands_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleanup completed: {telemetry_deleted} telemetry, {logs_deleted} logs, {commands_deleted} commands deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count telemetry records
            cursor.execute('SELECT COUNT(*) FROM telemetry')
            total_telemetry = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM telemetry WHERE sent = 0')
            unsent_telemetry = cursor.fetchone()[0]
            
            # Count commands
            cursor.execute('SELECT COUNT(*) FROM commands')
            total_commands = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM commands WHERE status = "pending"')
            pending_commands = cursor.fetchone()[0]
            
            # Count logs
            cursor.execute('SELECT COUNT(*) FROM logs')
            total_logs = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn.close()
            
            return {
                'database_path': self.db_path,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / 1024 / 1024, 2),
                'telemetry': {
                    'total': total_telemetry,
                    'unsent': unsent_telemetry,
                    'sent': total_telemetry - unsent_telemetry
                },
                'commands': {
                    'total': total_commands,
                    'pending': pending_commands,
                    'completed': total_commands - pending_commands
                },
                'logs': {
                    'total': total_logs
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
