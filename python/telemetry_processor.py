#!/usr/bin/env python3
"""
Telemetry Processor Module for ReliefWings Drone System
Handles telemetry data formatting, validation, and processing
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple

from datetime import datetime
import math

logger = logging.getLogger(__name__)


class TelemetryValidationRules:
    """Validation rules for telemetry data"""
    # lat_range: Tuple[float, float] = (-90.0, 90.0)
    # lng_range: Tuple[float, float] = (-180.0, 180.0)
    # alt_range: Tuple[float, float] = (-1000.0, 50000.0)  # Altitude
    # ground_speed: Tuple[float, float] = (0.0, 100.0)    # Ground Speed
    # vertical_speed: Tuple[float, float] = (-50.0, 50.0)  # Vertical Speed

    # heading_range: Tuple[float, float] = (0.0, 360.0)
    # battery_voltage_range: Tuple[float, float] = (0.0, 30.0)  # volts
    # battery_level_range: Tuple[int, int] = (0, 100)  # percentage
    # gps_fix_types: List[int] = [0, 1, 2, 3, 4, 5, 6]  # Valid GPS fix types
    # max_velocity: float = 100.0  # m/s
    # max_attitude_angle: float = 180.0  # degrees

    altitude: Tuple[float, float] = (-1000.0, 50000.0)  # Altitude in meters
    ground_speed: Tuple[float, float] = (0.0, 100.0)    # Ground Speed in m/s
    vertical_speed: Tuple[float, float] = (-50.0, 50.0)  # Vertical Speed in m/s
    distance_to_waypoint: Tuple[float, float] = (0.0, 100000.0)  # Distance in meters
    latitude: Tuple[float, float] = (-90.0, 90.0)       # Latitude in degrees
    longitude: Tuple[float, float] = (-180.0, 180.0)    # Longitude in degrees
    heading: Tuple[float, float] = (0.0, 360.0)         # Heading in degrees
    home_distance: Tuple[float, float] = (0.0, 100000.0) # Home distance in meters
    gps_signal: Tuple[float, float] = (0.0, 100.0)      # GPS signal strength
    satellite_count: Tuple[int, int] = (0, 12)          # Number of satellites
    battery_level: Tuple[int, int] = (0, 100)           # Battery level in percentage
    battery_voltage: Tuple[float, float] = (0.0, 30.0)   # Battery voltage in volts
    current: Tuple[float, float] = (0.0, 100.0)          # Current in amps
    throttle: Tuple[float, float] = (0.0, 100.0)        # Throttle in percentage
    pitch: Tuple[float, float] = (-90.0, 90.0)         # Pitch in degrees 
    roll: Tuple[float, float] = (-180.0, 180.0)        # Roll in degrees
    yaw: Tuple[float, float] = (0.0, 360.0)             # Yaw in degrees
    flight_mode: List[str] = ["MANUAL", "STABILIZE", "ALT_HOLD", "LOITER", "RTL", "AUTO", "GUIDED"]
    arm_status: List[bool] = [True, False]
    rssi: Tuple[int, int] = (0, 100)                   # RSSI in percentage (Recieved Signal Strength Indicator)
    wayPoints: Tuple[int, int] = (0, 100)              # Number of waypoints
    current_waypoint: Tuple[int, int] = (0, 100)     # Current waypoint index
    mission_progress: Tuple[float, float] = (0.0, 100.0) # Mission progress in percentage



#   airSpeed: number;
#   temperature: number;
#   windSpeed: number;
#   windDirection: number;

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

            # validate Altitude
            alt = data.get('alt', 0)
            if not (self.validation_rules.altitude[0] <= alt <= self.validation_rules.altitude[1]):
                errors.append(f"Invalid altitude: {alt}m")

            # ground speed
            gs = data.get('velocity', {}).get('ground_speed', 0)
            if not (self.validation_rules.ground_speed[0] <= gs <= self.validation_rules.ground_speed[1]):
                errors.append(f"Invalid ground speed: {gs}m/s")

            # vertical speed
            vs = data.get('velocity', {}).get('vz', 0)
            if not (self.validation_rules.vertical_speed[0] <= vs <= self.validation_rules.vertical_speed[1]):
                errors.append(f"Invalid vertical speed: {vs}m/s")

            # distance to waypoint
            dtw = data.get('distance_to_waypoint', 0)
            if not (self.validation_rules.distance_to_waypoint[0] <= dtw <= self.validation_rules.distance_to_waypoint[1]):
                errors.append(f"Invalid distance to waypoint: {dtw}m")

            # latitude
            lat = data.get('lat', 0)
            if not (self.validation_rules.latitude[0] <= lat <= self.validation_rules.latitude[1]):
                errors.append(f"Invalid latitude: {lat}°")
            # longitude
            lng = data.get('lng', 0)
            if not (self.validation_rules.longitude[0] <= lng <= self.validation_rules.longitude[1]):
                errors.append(f"Invalid longitude: {lng}°")
            # heading
            heading = data.get('heading', 0)
            if not (self.validation_rules.heading[0] <= heading <= self.validation_rules.heading[1]):
                errors.append(f"Invalid heading: {heading}°")
            # home distance
            hd = data.get('distance_from_home', 0)
            if not (self.validation_rules.home_distance[0] <= hd <= self.validation_rules.home_distance[1]):
                errors.append(f"Invalid home distance: {hd}m")
            # gps signal
            gps_signal = data.get('gps', {}).get('signal_strength', 0)
            if not (self.validation_rules.gps_signal[0] <= gps_signal <= self.validation_rules.gps_signal[1]):
                warnings.append(f"Unusual GPS signal strength: {gps_signal}%")
            # satellite count
            sat_count = data.get('gps', {}).get('satellites_visible', 0)
            if not (self.validation_rules.satellite_count[0] <= sat_count <= self.validation_rules.satellite_count[1]):
                warnings.append(f"Unusual satellite count: {sat_count}")
            # battery level
            battery_level = data.get('battery', {}).get('level', -1)
            if battery_level >= 0 and not (self.validation_rules.battery_level[0] <= battery_level <= self.validation_rules.battery_level[1]):
                errors.append(f"Invalid battery level: {battery_level}%")
            elif battery_level >= 0:
                if battery_level <= 10:
                    warnings.append(f"Critical battery level: {battery_level}%")
                elif battery_level <= 20:
                    warnings.append(f"Low battery level: {battery_level}%")
            # battery voltage
            battery_voltage = data.get('battery', {}).get('voltage', 0)
            if not (self.validation_rules.battery_voltage[0] <= battery_voltage <= self.validation_rules.battery_voltage[1]):
                if battery_voltage > 0:  # Only warn if voltage is positive
                    warnings.append(f"Unusual battery voltage: {battery_voltage}V")
            # current
            current = data.get('battery', {}).get('current', 0)
            if not (self.validation_rules.current[0] <= current <= self.validation_rules.current[1]):
                warnings.append(f"Unusual current draw: {current}A")
            # throttle
            throttle = data.get('throttle', 0)
            if not (self.validation_rules.throttle[0] <= throttle <= self.validation_rules.throttle[1]):
                warnings.append(f"Unusual throttle setting: {throttle}%")
            # pitch
            pitch = data.get('attitude', {}).get('pitch', 0)
            if not (self.validation_rules.pitch[0] <= pitch <= self.validation_rules.pitch[1]):
                errors.append(f"Invalid pitch angle: {pitch}°")
            # roll
            roll = data.get('attitude', {}).get('roll', 0)
            if not (self.validation_rules.roll[0] <= roll <= self.validation_rules.roll[1]):
                errors.append(f"Invalid roll angle: {roll}°")
            
            # yaw
            yaw = data.get('attitude', {}).get('yaw', 0)
            if not (self.validation_rules.yaw[0] <= yaw <= self.validation_rules.yaw[1]):
                errors.append(f"Invalid yaw angle: {yaw}°")
            # flight mode
            flight_mode = data.get('mode', '')
            if flight_mode not in self.validation_rules.flight_mode:
                errors.append(f"Invalid flight mode: {flight_mode}")
            # arm status
            armed = data.get('armed', None)
            if armed not in self.validation_rules.arm_status:
                errors.append(f"Invalid arm status: {armed}")
            
            # rssi
            rssi = data.get('rssi', 0)
            if not (self.validation_rules.rssi[0] <= rssi <= self.validation_rules.rssi[1]):
                warnings.append(f"Unusual RSSI: {rssi}%")
            # waypoints
            waypoints = data.get('waypoints', 0)
            if not (self.validation_rules.wayPoints[0] <= waypoints <= self.validation_rules.wayPoints[1]):
                warnings.append(f"Unusual number of waypoints: {waypoints}")
            # current waypoint
            current_wp = data.get('currentWaypoint', 0)
            if not (self.validation_rules.current_waypoint[0] <= current_wp <= self.validation_rules.current_waypoint[1]):
                warnings.append(f"Unusual current waypoint index: {current_wp}")
            # mission progress
            mission_progress = data.get('mission_progress', 0)
            if not (self.validation_rules.mission_progress[0] <= mission_progress <= self.validation_rules.mission_progress[1]):
                warnings.append(f"Unusual mission progress: {mission_progress}%")   
            # Validate timestamp
            ts = data.get('ts', 0)
            current_time = time.time()
            if abs(ts - current_time) > 60:  # More than 1 minute difference
                warnings.append(f"Timestamp deviation: {ts - current_time:.1f}s")
            
            
            required_fields = ['drone_id', 'ts', 'seq', 'lat', 'lng', 'alt', 'mode', 'armed']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # validate data types
            if 'seq' in data and not isinstance(data['seq'], int):
                try:
                    data['seq'] = int(data['seq'])
                except ValueError:
                    errors.append("Invalid sequence number type")

            if 'armed' in data and not isinstance(data['armed'], bool):
                data['armed'] = bool(data['armed'])

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
            # Ensure nested dicts exist
            for key in ['velocity', 'attitude', 'battery', 'gps', 'sensors']:
                if key not in data or not isinstance(data.get(key), dict):
                    data[key] = {}
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
        """Format telemetry data for database storage according to TelemetryValidationRules"""
        try:
            db_data = data.copy()
            # Remove processing-specific fields
            fields_to_remove = [
                'processing_error', 'processed_at', 'processing_latency',
                'validation', 'signal_quality'
            ]
            for field in fields_to_remove:
                db_data.pop(field, None)

            # Ensure all fields in TelemetryValidationRules are present and properly typed
            rules = asdict(self.validation_rules)
            for field, rule in rules.items():
                if field in db_data:
                    # Handle numeric fields (tuple or list means range)
                    if isinstance(rule, (tuple, list)):
                        # Try to cast to int if both bounds are int, else float
                        if all(isinstance(x, int) for x in rule):
                            try:
                                db_data[field] = int(db_data[field])
                            except Exception:
                                logger.warning(f"Could not convert {field} to int: {db_data[field]}")
                        else:
                            try:
                                db_data[field] = float(db_data[field])
                            except Exception:
                                logger.warning(f"Could not convert {field} to float: {db_data[field]}")
                    # Handle enum/list fields (like flight_mode, arm_status)
                    elif isinstance(rule, list):
                        # No conversion, just ensure present
                        pass

            # Optionally, keep only fields defined in TelemetryValidationRules and a few required fields
            required_fields = ['drone_id', 'ts', 'seq', 'mode', 'armed']
            allowed_fields = set(rules.keys()).union(required_fields)
            db_data = {k: v for k, v in db_data.items() if k in allowed_fields or isinstance(v, dict)}

            return db_data

        except Exception as e:
            logger.error(f"Failed to format telemetry for database: {e}")
            return data
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
