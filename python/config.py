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
    connection_string: str = "/dev/ttyACM0"
    baud_rate: int = 115200
    connection_timeout: int = 30
    heartbeat_timeout: int = 15

@dataclass
class WebSocketConfig:
    """WebSocket configuration settings"""
    server_url: str = "ws://localhost:8080"
    api_key: str = None  # Authentication key
    reconnect_attempts: int = 5
    reconnect_delay: int = 5
    ping_interval: int = 30
    pong_timeout: int = 10
    max_reconnect_delay: int = 60  # Maximum delay for exponential backoff

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
    validation_enabled: bool = True  # Enable telemetry validation
    auto_cleanup_interval: int = 3600  # Automatic cleanup interval (seconds)
    
class SystemConfig:
    # Main system configuration manager
    
    def __init__(self):
        # Load configuration from environment variables with defaults
        self.drone = DroneConfig(
            drone_id=os.environ.get('DRONE_ID', 'DRONE_001'),
            connection_string=os.environ.get('VEHICLE_CONNECTION', '/dev/ttyACM0'),
            baud_rate=int(os.environ.get('VEHICLE_BAUD_RATE', '57600')),
            connection_timeout=int(os.environ.get('VEHICLE_TIMEOUT', '30')),
            heartbeat_timeout=int(os.environ.get('HEARTBEAT_TIMEOUT', '15'))
        )
        
        self.websocket = WebSocketConfig(
            server_url=os.environ.get('WEBSOCKET_URL', 'ws://localhost:8080'),
            api_key=os.environ.get('API_KEY'),
            reconnect_attempts=int(os.environ.get('WS_RECONNECT_ATTEMPTS', '5')),
            reconnect_delay=int(os.environ.get('WS_RECONNECT_DELAY', '5')),
            ping_interval=int(os.environ.get('WS_PING_INTERVAL', '30')),
            pong_timeout=int(os.environ.get('WS_PONG_TIMEOUT', '10')),
            max_reconnect_delay=int(os.environ.get('WS_MAX_RECONNECT_DELAY', '60'))
        )
        
        self.database = DatabaseConfig(
            db_path=os.environ.get('DATABASE_PATH', '/tmp/drone_telemetry.db'),
            cleanup_days=int(os.environ.get('DB_CLEANUP_DAYS', '7')),
            max_buffer_size=int(os.environ.get('DB_BUFFER_SIZE', '1000'))
        )
        
        self.telemetry = TelemetryConfig(
            collection_interval=float(os.environ.get('TELEMETRY_INTERVAL', '1.0')),
            health_check_interval=int(os.environ.get('HEALTH_CHECK_INTERVAL', '30')),
            max_history_size=int(os.environ.get('TELEMETRY_HISTORY_SIZE', '100')),
            validation_enabled=os.environ.get('TELEMETRY_VALIDATION', 'true').lower() == 'true',
            auto_cleanup_interval=int(os.environ.get('AUTO_CLEANUP_INTERVAL', '3600'))
        )
        
        # Logging configuration
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        self.log_file = os.environ.get('LOG_FILE', '/tmp/drone_telemetry.log')
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration settings and return validation results"""
        issues = []
        warnings = []
        
        # Validate drone configuration
        if not self.drone.drone_id:
            issues.append("Drone ID cannot be empty")
        
        if self.drone.connection_timeout < 5:
            warnings.append("Connection timeout is very low (< 5 seconds)")
        
        # Validate WebSocket configuration  
        if not self.websocket.server_url.startswith(('ws://', 'wss://')):
            issues.append("WebSocket URL must start with ws:// or wss://")
        
        if self.websocket.reconnect_attempts < 1:
            issues.append("Reconnect attempts must be at least 1")
        
        # Validate telemetry configuration
        if self.telemetry.collection_interval < 0.1:
            warnings.append("Very fast telemetry collection interval (< 0.1s) may impact performance")
        
        if self.telemetry.collection_interval > 10:
            warnings.append("Slow telemetry collection interval (> 10s) may miss important data")
        
        # Validate database configuration
        db_dir = os.path.dirname(self.database.db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception:
                issues.append(f"Cannot create database directory: {db_dir}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about environment variables used"""
        env_vars = [
            'DRONE_ID', 'VEHICLE_CONNECTION', 'VEHICLE_BAUD_RATE', 'VEHICLE_TIMEOUT', 
            'HEARTBEAT_TIMEOUT', 'WEBSOCKET_URL', 'API_KEY', 'WS_RECONNECT_ATTEMPTS',
            'WS_RECONNECT_DELAY', 'WS_PING_INTERVAL', 'WS_PONG_TIMEOUT', 'WS_MAX_RECONNECT_DELAY',
            'DATABASE_PATH', 'DB_CLEANUP_DAYS', 'DB_BUFFER_SIZE', 'TELEMETRY_INTERVAL',
            'HEALTH_CHECK_INTERVAL', 'TELEMETRY_HISTORY_SIZE', 'TELEMETRY_VALIDATION',
            'AUTO_CLEANUP_INTERVAL', 'LOG_LEVEL', 'LOG_FILE'
        ]
        
        return {
            'environment_variables': {
                var: os.environ.get(var, 'Not set') for var in env_vars
            },
            'using_defaults': [
                var for var in env_vars if var not in os.environ
            ]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert configuration to dictionary
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
                'api_key': self.websocket.api_key,
                'reconnect_attempts': self.websocket.reconnect_attempts,
                'reconnect_delay': self.websocket.reconnect_delay,
                'ping_interval': self.websocket.ping_interval,
                'pong_timeout': self.websocket.pong_timeout,
                'max_reconnect_delay': self.websocket.max_reconnect_delay
            },
            'database': {
                'db_path': self.database.db_path,
                'cleanup_days': self.database.cleanup_days,
                'max_buffer_size': self.database.max_buffer_size
            },
            'telemetry': {
                'collection_interval': self.telemetry.collection_interval,
                'health_check_interval': self.telemetry.health_check_interval,
                'max_history_size': self.telemetry.max_history_size,
                'validation_enabled': self.telemetry.validation_enabled,
                'auto_cleanup_interval': self.telemetry.auto_cleanup_interval
            },
            'logging': {
                'log_level': self.log_level,
                'log_file': self.log_file
            }
        }

# Global configuration instance
config = SystemConfig()
