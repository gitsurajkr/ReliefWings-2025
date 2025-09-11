#!/usr/bin/env python3
"""
Telemetry Processor Module for ReliefWings Drone System
Handles telemetry data formatting, validation, and processing
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import math

logger = logging.getLogger(__name__)

@dataclass
class TelemetryValidationRules:
    """Validation rules for telemetry data"""
    lat_range: Tuple[float, float] = (-90.0, 90.0)
    lng_range: Tuple[float, float] = (-180.0, 180.0)
    alt_range: Tuple[float, float] = (-1000.0, 50000.0)  # meters
    heading_range: Tuple[float, float] = (0.0, 360.0)
    battery_voltage_range: Tuple[float, float] = (0.0, 30.0)  # volts
    battery_level_range: Tuple[int, int] = (0, 100)  # percentage
    gps_fix_types: List[int] = [0, 1, 2, 3, 4, 5, 6]  # Valid GPS fix types
    max_velocity: float = 100.0  # m/s
    max_attitude_angle: float = 180.0  # degrees

class TelemetryProcessor:
    """Processes and validates drone telemetry data"""
    
    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        self.validation_rules = TelemetryValidationRules()
        self.last_telemetry: Optional[Dict[str, Any]] = None
        self.telemetry_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        self.validation_errors = []
        self.stats = {
            'total_processed': 0,
            'validation_errors': 0,
            'last_processed': None
        }
    
    def process_telemetry(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate telemetry data"""
        try:
            # Add processing timestamp
            processed_data = telemetry_data.copy()
            processed_data['processed_at'] = time.time()
            processed_data['processing_latency'] = processed_data['processed_at'] - telemetry_data.get('ts', 0)
            
            # Validate data
            validation_result = self.validate_telemetry(processed_data)
            processed_data['validation'] = validation_result
            
            # Add derived data
            processed_data = self._add_derived_data(processed_data)
            
            # Update history
            self._update_history(processed_data)
            
            # Update statistics
            self.stats['total_processed'] += 1
            self.stats['last_processed'] = time.time()
            
            if not validation_result['is_valid']:
                self.stats['validation_errors'] += 1
            
            self.last_telemetry = processed_data
            
            logger.debug(f"Processed telemetry for drone {self.drone_id}, seq {telemetry_data.get('seq', 0)}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to process telemetry: {e}")
            # Return original data with error flag
            error_data = telemetry_data.copy()
            error_data['processing_error'] = str(e)
            error_data['validation'] = {'is_valid': False, 'errors': [str(e)]}
            return error_data
    
    def validate_telemetry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate telemetry data against rules"""
        errors = []
        warnings = []
        
        try:
            # Validate latitude
            lat = data.get('lat', 0)
            if not (self.validation_rules.lat_range[0] <= lat <= self.validation_rules.lat_range[1]):
                errors.append(f"Invalid latitude: {lat}")
            
            # Validate longitude
            lng = data.get('lng', 0)
            if not (self.validation_rules.lng_range[0] <= lng <= self.validation_rules.lng_range[1]):
                errors.append(f"Invalid longitude: {lng}")
            
            # Validate altitude
            alt = data.get('alt', 0)
            if not (self.validation_rules.alt_range[0] <= alt <= self.validation_rules.alt_range[1]):
                errors.append(f"Invalid altitude: {alt}")
            
            # Validate heading
            heading = data.get('heading', 0)
            if not (0 <= heading <= 360):
                # Normalize heading
                heading = heading % 360
                data['heading'] = heading
                warnings.append(f"Normalized heading to {heading}")
            
            # Validate velocity
            velocity = data.get('velocity', {})
            if isinstance(velocity, dict):
                for vel_component in ['vx', 'vy', 'vz']:
                    vel_value = velocity.get(vel_component, 0)
                    if abs(vel_value) > self.validation_rules.max_velocity:
                        warnings.append(f"High {vel_component} velocity: {vel_value} m/s")
                
                ground_speed = velocity.get('ground_speed', 0)
                if ground_speed > self.validation_rules.max_velocity:
                    warnings.append(f"High ground speed: {ground_speed} m/s")
            
            # Validate attitude
            attitude = data.get('attitude', {})
            if isinstance(attitude, dict):
                for angle_name in ['roll', 'pitch', 'yaw']:
                    angle_value = attitude.get(angle_name, 0)
                    if abs(angle_value) > self.validation_rules.max_attitude_angle:
                        errors.append(f"Invalid {angle_name} angle: {angle_value}")
            
            # Validate battery
            battery = data.get('battery', {})
            if isinstance(battery, dict):
                voltage = battery.get('voltage', 0)
                if not (self.validation_rules.battery_voltage_range[0] <= voltage <= self.validation_rules.battery_voltage_range[1]):
                    if voltage > 0:  # Only warn if voltage is positive
                        warnings.append(f"Unusual battery voltage: {voltage}V")
                
                level = battery.get('level', -1)
                if level >= 0 and not (self.validation_rules.battery_level_range[0] <= level <= self.validation_rules.battery_level_range[1]):
                    errors.append(f"Invalid battery level: {level}%")
                
                # Battery level warnings
                if level >= 0:
                    if level <= 10:
                        warnings.append(f"Critical battery level: {level}%")
                    elif level <= 20:
                        warnings.append(f"Low battery level: {level}%")
            
            # Validate GPS
            gps = data.get('gps', {})
            if isinstance(gps, dict):
                fix_type = gps.get('fix_type', 0)
                if fix_type not in self.validation_rules.gps_fix_types:
                    errors.append(f"Invalid GPS fix type: {fix_type}")
                elif fix_type < 2:
                    warnings.append(f"Poor GPS fix: {fix_type}")
                
                satellites = gps.get('satellites_visible', 0)
                if satellites < 4:
                    warnings.append(f"Low satellite count: {satellites}")
            
            # Validate timestamp
            ts = data.get('ts', 0)
            current_time = time.time()
            if abs(ts - current_time) > 60:  # More than 1 minute difference
                warnings.append(f"Timestamp deviation: {ts - current_time:.1f}s")
            
            # Check for required fields
            required_fields = ['drone_id', 'ts', 'seq', 'lat', 'lng', 'alt', 'mode', 'armed']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Validate data types
            if 'seq' in data and not isinstance(data['seq'], int):
                try:
                    data['seq'] = int(data['seq'])
                except ValueError:
                    errors.append("Invalid sequence number type")
            
            if 'armed' in data and not isinstance(data['armed'], bool):
                data['armed'] = bool(data['armed'])
            
            # Store validation errors for analysis
            if errors:
                self.validation_errors.extend(errors)
                # Keep only last 100 errors
                self.validation_errors = self.validation_errors[-100:]
            
            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'validated_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation exception: {e}"],
                'warnings': [],
                'validated_at': time.time()
            }
    
    def _add_derived_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add derived/calculated data to telemetry"""
        try:
            # Calculate distance from home (if we have previous data)
            if self.last_telemetry and 'lat' in data and 'lng' in data:
                home_lat = self.last_telemetry.get('lat', data['lat'])
                home_lng = self.last_telemetry.get('lng', data['lng'])
                
                distance_from_home = self._calculate_distance(
                    data['lat'], data['lng'],
                    home_lat, home_lng
                )
                data['distance_from_home'] = distance_from_home
            
            # Calculate 3D velocity magnitude
            velocity = data.get('velocity', {})
            if isinstance(velocity, dict):
                vx = velocity.get('vx', 0)
                vy = velocity.get('vy', 0)
                vz = velocity.get('vz', 0)
                velocity_3d = math.sqrt(vx**2 + vy**2 + vz**2)
                data['velocity']['velocity_3d'] = velocity_3d
            
            # Add flight time (if armed)
            if data.get('armed', False) and self.last_telemetry:
                if self.last_telemetry.get('armed', False):
                    # Continue flight time
                    last_flight_time = self.last_telemetry.get('flight_time', 0)
                    time_diff = data['ts'] - self.last_telemetry['ts']
                    data['flight_time'] = last_flight_time + time_diff
                else:
                    # Start of new flight
                    data['flight_time'] = 0
            else:
                data['flight_time'] = 0
            
            # Add signal quality indicator
            gps = data.get('gps', {})
            if isinstance(gps, dict):
                fix_type = gps.get('fix_type', 0)
                satellites = gps.get('satellites_visible', 0)
                
                if fix_type >= 3 and satellites >= 8:
                    signal_quality = "excellent"
                elif fix_type >= 2 and satellites >= 6:
                    signal_quality = "good"
                elif fix_type >= 2 and satellites >= 4:
                    signal_quality = "fair"
                else:
                    signal_quality = "poor"
                
                data['signal_quality'] = signal_quality
            
            # Add battery health estimate
            battery = data.get('battery', {})
            if isinstance(battery, dict):
                voltage = battery.get('voltage', 0)
                level = battery.get('level', -1)
                
                if level >= 0:
                    if level > 80:
                        battery_health = "excellent"
                    elif level > 60:
                        battery_health = "good"
                    elif level > 40:
                        battery_health = "fair"
                    elif level > 20:
                        battery_health = "low"
                    else:
                        battery_health = "critical"
                    
                    data['battery']['health'] = battery_health
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to add derived data: {e}")
            return data
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS coordinates (Haversine formula)"""
        try:
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lng1_rad = math.radians(lng1)
            lat2_rad = math.radians(lat2)
            lng2_rad = math.radians(lng2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlng = lng2_rad - lng1_rad
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth radius in meters
            earth_radius = 6371000
            
            return earth_radius * c
            
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return 0.0
    
    def _update_history(self, data: Dict[str, Any]):
        """Update telemetry history"""
        self.telemetry_history.append(data)
        
        # Keep only recent history
        if len(self.telemetry_history) > self.max_history_size:
            self.telemetry_history = self.telemetry_history[-self.max_history_size:]
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get summary of telemetry processing"""
        return {
            'drone_id': self.drone_id,
            'stats': self.stats.copy(),
            'last_telemetry': self.last_telemetry,
            'history_size': len(self.telemetry_history),
            'recent_validation_errors': self.validation_errors[-10:] if self.validation_errors else [],
            'processing_health': {
                'error_rate': (self.stats['validation_errors'] / max(self.stats['total_processed'], 1)) * 100,
                'last_update': self.stats['last_processed']
            }
        }
    
    def format_for_websocket(self, data: Dict[str, Any]) -> str:
        """Format telemetry data for WebSocket transmission"""
        try:
            # Create a clean copy for transmission
            clean_data = {
                'type': 'telemetry',
                'drone_id': data.get('drone_id'),
                'timestamp': data.get('ts'),
                'seq': data.get('seq'),
                'location': {
                    'lat': data.get('lat'),
                    'lng': data.get('lng'),
                    'alt': data.get('alt'),
                    'heading': data.get('heading')
                },
                'velocity': data.get('velocity', {}),
                'attitude': data.get('attitude', {}),
                'battery': data.get('battery', {}),
                'gps': data.get('gps', {}),
                'flight': {
                    'mode': data.get('mode'),
                    'armed': data.get('armed'),
                    'system_status': data.get('system_status'),
                    'flight_time': data.get('flight_time', 0)
                },
                'sensors': data.get('sensors', {}),
                'derived': {
                    'signal_quality': data.get('signal_quality'),
                    'distance_from_home': data.get('distance_from_home')
                },
                'validation': {
                    'is_valid': data.get('validation', {}).get('is_valid', True),
                    'warnings': data.get('validation', {}).get('warnings', [])
                }
            }
            
            return json.dumps(clean_data)
            
        except Exception as e:
            logger.error(f"Failed to format telemetry for WebSocket: {e}")
            return json.dumps({
                'type': 'error',
                'drone_id': data.get('drone_id'),
                'error': f"Format error: {e}"
            })
    
    def format_for_database(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format telemetry data for database storage"""
        try:
            # Remove processing-specific fields that don't need storage
            db_data = data.copy()
            
            # Remove large or temporary fields
            fields_to_remove = ['processing_error', 'processed_at', 'processing_latency']
            for field in fields_to_remove:
                db_data.pop(field, None)
            
            # Ensure all numeric fields are properly typed
            numeric_fields = ['lat', 'lng', 'alt', 'heading', 'ts', 'seq']
            for field in numeric_fields:
                if field in db_data:
                    try:
                        if field == 'seq':
                            db_data[field] = int(db_data[field])
                        else:
                            db_data[field] = float(db_data[field])
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {field} to numeric: {db_data[field]}")
            
            return db_data
            
        except Exception as e:
            logger.error(f"Failed to format telemetry for database: {e}")
            return data
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get processor health metrics"""
        current_time = time.time()
        
        return {
            'processor_id': f"{self.drone_id}_processor",
            'uptime': current_time - (self.stats['last_processed'] or current_time),
            'total_processed': self.stats['total_processed'],
            'error_rate': (self.stats['validation_errors'] / max(self.stats['total_processed'], 1)) * 100,
            'last_activity': self.stats['last_processed'],
            'history_size': len(self.telemetry_history),
            'validation_rules': asdict(self.validation_rules),
            'recent_errors': len(self.validation_errors),
            'status': 'healthy' if self.stats['total_processed'] > 0 else 'inactive'
        }
