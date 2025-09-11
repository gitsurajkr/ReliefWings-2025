#!/usr/bin/env python3
"""
Configuration Module for ReliefWings Drone System
Centralized configuration management
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DroneConfig:
    """Drone configuration settings"""
    drone_id: str = "DRONE_001"
    connection_string: str = "/dev/ttyUSB0"
    baud_rate: int = 57600
    connection_timeout: int = 30
    heartbeat_timeout: int = 15

@dataclass
class WebSocketConfig:
    """WebSocket configuration settings"""
    server_url: str = "ws://localhost:8080"
    reconnect_attempts: int = 5
    reconnect_delay: int = 5
    ping_interval: int = 30
    pong_timeout: int = 10

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    db_path: str = "/tmp/drone_telemetry.db"
    cleanup_days: int = 7
    max_buffer_size: int = 1000

@dataclass
class TelemetryConfig:
    """Telemetry configuration settings"""
    collection_interval: float = 1.0  # seconds
    health_check_interval: int = 30  # seconds
    max_history_size: int = 100
    
class SystemConfig:
    """Main system configuration manager"""
    
    def __init__(self):
        # Load configuration from environment variables with defaults
        self.drone = DroneConfig(
            drone_id=os.environ.get('DRONE_ID', 'DRONE_001'),
            connection_string=os.environ.get('VEHICLE_CONNECTION', '/dev/ttyUSB0'),
            baud_rate=int(os.environ.get('VEHICLE_BAUD_RATE', '57600')),
            connection_timeout=int(os.environ.get('VEHICLE_TIMEOUT', '30')),
            heartbeat_timeout=int(os.environ.get('HEARTBEAT_TIMEOUT', '15'))
        )
        
        self.websocket = WebSocketConfig(
            server_url=os.environ.get('WEBSOCKET_URL', 'ws://localhost:8080'),
            reconnect_attempts=int(os.environ.get('WS_RECONNECT_ATTEMPTS', '5')),
            reconnect_delay=int(os.environ.get('WS_RECONNECT_DELAY', '5')),
            ping_interval=int(os.environ.get('WS_PING_INTERVAL', '30')),
            pong_timeout=int(os.environ.get('WS_PONG_TIMEOUT', '10'))
        )
        
        self.database = DatabaseConfig(
            db_path=os.environ.get('DATABASE_PATH', '/tmp/drone_telemetry.db'),
            cleanup_days=int(os.environ.get('DB_CLEANUP_DAYS', '7')),
            max_buffer_size=int(os.environ.get('DB_BUFFER_SIZE', '1000'))
        )
        
        self.telemetry = TelemetryConfig(
            collection_interval=float(os.environ.get('TELEMETRY_INTERVAL', '1.0')),
            health_check_interval=int(os.environ.get('HEALTH_CHECK_INTERVAL', '30')),
            max_history_size=int(os.environ.get('TELEMETRY_HISTORY_SIZE', '100'))
        )
        
        # Logging configuration
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        self.log_file = os.environ.get('LOG_FILE', '/tmp/drone_telemetry.log')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'drone': {
                'drone_id': self.drone.drone_id,
                'connection_string': self.drone.connection_string,
                'baud_rate': self.drone.baud_rate,
                'connection_timeout': self.drone.connection_timeout,
                'heartbeat_timeout': self.drone.heartbeat_timeout
            },
            'websocket': {
                'server_url': self.websocket.server_url,
                'reconnect_attempts': self.websocket.reconnect_attempts,
                'reconnect_delay': self.websocket.reconnect_delay,
                'ping_interval': self.websocket.ping_interval,
                'pong_timeout': self.websocket.pong_timeout
            },
            'database': {
                'db_path': self.database.db_path,
                'cleanup_days': self.database.cleanup_days,
                'max_buffer_size': self.database.max_buffer_size
            },
            'telemetry': {
                'collection_interval': self.telemetry.collection_interval,
                'health_check_interval': self.telemetry.health_check_interval,
                'max_history_size': self.telemetry.max_history_size
            },
            'logging': {
                'log_level': self.log_level,
                'log_file': self.log_file
            }
        }

# Global configuration instance
config = SystemConfig()
