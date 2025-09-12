"""
Drone Controller Module for ReliefWings Telemetry System
Handles DroneKit vehicle operations and command execution
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum
import time
import math

# DroneKit imports
from dronekit import connect, Vehicle, LocationGlobalRelative, LocationGlobal
from pymavlink import mavutil

logger = logging.getLogger(__name__)

class DroneStatus(Enum):
    """Drone connection and flight status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ARMED = "armed"
    DISARMED = "disarmed"
    IN_FLIGHT = "in_flight"
    LANDED = "landed"
    ERROR = "error"

class TelemetryData:
    """Structured telemetry data"""
    drone_id: str
    ts: float
    seq: int
    lat: float
    lng: float
    alt: float
    heading: float
    velocity: Dict[str, float]
    attitude: Dict[str, float]
    battery: Dict[str, Union[int, float]]
    gps: Dict[str, Any]
    mode: str
    armed: bool
    system_status: str
    sensors: Dict[str, bool]

class DroneController:
    """DroneKit vehicle controller for telemetry and command execution"""
    
    def __init__(self, drone_id: str, connection_string: str = "/dev/ttyUSB0"):
        self.drone_id = drone_id
        self.connection_string = connection_string
        self.vehicle: Optional[Vehicle] = None
        self.status = DroneStatus.DISCONNECTED
        self.last_telemetry: Optional[TelemetryData] = None
        self.seq_number = 0
        
        # Callbacks
        self.telemetry_callback: Optional[Callable[[TelemetryData], None]] = None
        self.status_callback: Optional[Callable[[DroneStatus, str], None]] = None
        self.command_result_callback: Optional[Callable[[int, str, Dict[str, Any]], None]] = None
        
        # Connection monitoring
        self.last_heartbeat = 0
        self.heartbeat_timeout = 10  # seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
    
    def set_telemetry_callback(self, callback: Callable[[TelemetryData], None]):
        """Set callback for telemetry data"""
        self.telemetry_callback = callback
    
    def set_status_callback(self, callback: Callable[[DroneStatus, str], None]):
        # Set callback for status changes
        self.status_callback = callback
    
    def set_command_result_callback(self, callback: Callable[[int, str, Dict[str, Any]], None]):
        """Set callback for command results"""
        self.command_result_callback = callback
    
    async def connect_to_vehicle(self) -> bool:
        """Connect to the drone via DroneKit"""
        try:
            self._update_status(DroneStatus.CONNECTING, "Attempting to connect to vehicle...")
            
            # Connect to vehicle
            self.vehicle = connect(
                self.connection_string,
                wait_ready=True,
                timeout=30,
                heartbeat_timeout=15
            )
            
            if self.vehicle is None:
                raise Exception("Failed to establish vehicle connection")
            
            # Set up vehicle attribute listeners
            self._setup_vehicle_listeners()
            
            self.last_heartbeat = time.time()
            self.reconnect_attempts = 0
            self._update_status(DroneStatus.CONNECTED, f"Connected to vehicle at {self.connection_string}")
            
            logger.info(f"Successfully connected to drone {self.drone_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to vehicle: {e}"
            self._update_status(DroneStatus.ERROR, error_msg)
            logger.error(error_msg)
            return False
    
    def _setup_vehicle_listeners(self):
        """Set up DroneKit vehicle attribute listeners"""
        if not self.vehicle:
            return
        
        # Set up attribute listeners for real-time updates
        @self.vehicle.on_attribute('location.global_relative_frame')
        def location_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('location', value)
        
        @self.vehicle.on_attribute('attitude')
        def attitude_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('attitude', value)
        
        @self.vehicle.on_attribute('velocity')
        def velocity_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('velocity', value)
        
        @self.vehicle.on_attribute('battery')
        def battery_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('battery', value)
        
        @self.vehicle.on_attribute('armed')
        def armed_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('armed', value)
        
        @self.vehicle.on_attribute('mode')
        def mode_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('mode', value)
        
        @self.vehicle.on_attribute('system_status')
        def system_status_listener(self_vehicle, attr_name, value):
            self._on_attribute_change('system_status', value)
    
    def _on_attribute_change(self, attr_name: str, value):
        """Handle vehicle attribute changes"""
        self.last_heartbeat = time.time()
        
        # Update status based on vehicle state
        if self.vehicle:
            if self.vehicle.armed:
                self._update_status(DroneStatus.ARMED, "Vehicle is armed")
            else:
                self._update_status(DroneStatus.DISARMED, "Vehicle is disarmed")
    
    def _update_status(self, status: DroneStatus, message: str):
        """Update drone status and notify callback"""
        self.status = status
        logger.info(f"Drone {self.drone_id} status: {status.value} - {message}")
        
        if self.status_callback:
            try:
                self.status_callback(status, message)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def get_telemetry_data(self) -> Optional[TelemetryData]:
        """Get current telemetry data from vehicle and log all fields with try/except."""
        if not self.vehicle:
            return None
        try:
            self.seq_number += 1
            # Get location data
            try:
                location = self.vehicle.location.global_relative_frame
                if location is None:
                    location = LocationGlobalRelative(0, 0, 0)
            except Exception as e:
                logger.error(f"Error getting location: {e}")
                location = LocationGlobalRelative(0, 0, 0)

            # Get attitude data
            try:
                attitude = self.vehicle.attitude
                attitude_dict = {
                    'roll': math.degrees(attitude.roll) if attitude else 0,
                    'pitch': math.degrees(attitude.pitch) if attitude else 0,
                    'yaw': math.degrees(attitude.yaw) if attitude else 0
                }
            except Exception as e:
                logger.error(f"Error getting attitude: {e}")
                attitude_dict = {'roll': 0, 'pitch': 0, 'yaw': 0}

            # Get velocity data
            try:
                velocity = self.vehicle.velocity
                velocity_dict = {
                    'vx': velocity[0] if velocity and len(velocity) > 0 else 0,
                    'vy': velocity[1] if velocity and len(velocity) > 1 else 0,
                    'vz': velocity[2] if velocity and len(velocity) > 2 else 0,
                    'ground_speed': math.sqrt(velocity[0]**2 + velocity[1]**2) if velocity and len(velocity) >= 2 else 0
                }
            except Exception as e:
                logger.error(f"Error getting velocity: {e}")
                velocity_dict = {'vx': 0, 'vy': 0, 'vz': 0, 'ground_speed': 0}

            # Get battery data
            try:
                battery = self.vehicle.battery
                battery_dict = {
                    'voltage': float(battery.voltage) if battery and battery.voltage else 0.0,
                    'current': float(battery.current) if battery and battery.current else 0.0,
                    'level': int(battery.level) if battery and battery.level is not None else -1,
                    'remaining': int(battery.level) if battery and battery.level is not None else -1
                }
            except Exception as e:
                logger.error(f"Error getting battery: {e}")
                battery_dict = {'voltage': 0.0, 'current': 0.0, 'level': -1, 'remaining': -1}

            # Get GPS data
            try:
                gps = self.vehicle.gps_0
                gps_dict = {
                    'fix_type': int(gps.fix_type) if gps else 0,
                    'satellites_visible': int(gps.satellites_visible) if gps else 0,
                    'eph': float(gps.eph) if gps else 9999,
                    'epv': float(gps.epv) if gps else 9999
                }
            except Exception as e:
                logger.error(f"Error getting GPS: {e}")
                gps_dict = {'fix_type': 0, 'satellites_visible': 0, 'eph': 9999, 'epv': 9999}

            # Get sensor health
            try:
                sensors = {
                    'accelerometer': True,  # Assume healthy if connected
                    'gyroscope': True,
                    'magnetometer': True,
                    'barometer': True,
                    'gps': gps_dict['fix_type'] >= 2 if gps_dict else False
                }
            except Exception as e:
                logger.error(f"Error getting sensors: {e}")
                sensors = {'accelerometer': False, 'gyroscope': False, 'magnetometer': False, 'barometer': False, 'gps': False}

            # Create telemetry data structure
            telemetry = TelemetryData(
                drone_id=self.drone_id,
                ts=time.time(),
                seq=self.seq_number,
                lat=float(location.lat),
                lng=float(location.lon),
                alt=float(location.alt),
                heading=attitude_dict['yaw'],
                velocity=velocity_dict,
                attitude=attitude_dict,
                battery=battery_dict,
                gps=gps_dict,
                mode=str(self.vehicle.mode.name) if self.vehicle and self.vehicle.mode else "UNKNOWN",
                armed=bool(self.vehicle.armed) if self.vehicle else False,
                system_status=str(self.vehicle.system_status.state) if self.vehicle and self.vehicle.system_status else "UNKNOWN",
                sensors=sensors
            )
            self.last_telemetry = telemetry
            # Log all telemetry data to console
            logger.info(f"TelemetryData: {telemetry}")
            # Notify callback
            if self.telemetry_callback:
                try:
                    self.telemetry_callback(telemetry)
                except Exception as e:
                    logger.error(f"Telemetry callback error: {e}")
            return telemetry
        except Exception as e:
            logger.error(f"Failed to get telemetry data: {e}")
            return None
    
    async def execute_command(self, command_id: int, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a drone command"""
        if not self.vehicle:
            result = {"success": False, "error": "Vehicle not connected"}
            self._notify_command_result(command_id, "failed", result)
            return result
        
        try:
            logger.info(f"Executing command {command} for drone {self.drone_id}")
            result = {"success": True}
            
            if command == "arm":
                result = await self._arm_vehicle()
            elif command == "disarm":
                result = await self._disarm_vehicle()
            elif command == "takeoff":
                altitude = args.get('altitude', 10) if args else 10
                result = await self._takeoff(altitude)
            elif command == "land":
                result = await self._land()
            elif command == "goto":
                if args and 'lat' in args and 'lng' in args:
                    lat = args['lat']
                    lng = args['lng']
                    alt = args.get('alt', self.last_telemetry.alt if self.last_telemetry else 10)
                    result = await self._goto_location(lat, lng, alt)
                else:
                    result = {"success": False, "error": "Missing lat/lng coordinates"}
            elif command == "set_mode":
                mode = args.get('mode', 'GUIDED') if args else 'GUIDED'
                result = await self._set_mode(mode)
            elif command == "rtl":
                result = await self._return_to_launch()
            elif command == "get_status":
                result = self._get_vehicle_status()
            else:
                result = {"success": False, "error": f"Unknown command: {command}"}
            
            status = "completed" if result["success"] else "failed"
            self._notify_command_result(command_id, status, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            logger.error(error_msg)
            result = {"success": False, "error": error_msg}
            self._notify_command_result(command_id, "failed", result)
            return result
    
    def _notify_command_result(self, command_id: int, status: str, result: Dict[str, Any]):
        """Notify command result via callback"""
        if self.command_result_callback:
            try:
                self.command_result_callback(command_id, status, result)
            except Exception as e:
                logger.error(f"Command result callback error: {e}")
    
    async def _arm_vehicle(self) -> Dict[str, Any]:
        """Arm the vehicle"""
        try:
            if self.vehicle.armed:
                return {"success": True, "message": "Vehicle already armed"}
            
            # Check if vehicle is armable
            while not self.vehicle.is_armable:
                logger.info("Waiting for vehicle to become armable...")
                await asyncio.sleep(1)
            
            # Arm vehicle
            self.vehicle.armed = True
            
            # Wait for arming confirmation
            timeout = 30
            start_time = time.time()
            while not self.vehicle.armed and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
            
            if self.vehicle.armed:
                return {"success": True, "message": "Vehicle armed successfully"}
            else:
                return {"success": False, "error": "Failed to arm vehicle within timeout"}
                
        except Exception as e:
            return {"success": False, "error": f"Arming failed: {e}"}
    
    async def _disarm_vehicle(self) -> Dict[str, Any]:
        """Disarm the vehicle"""
        try:
            if not self.vehicle.armed:
                return {"success": True, "message": "Vehicle already disarmed"}
            
            # Disarm vehicle
            self.vehicle.armed = False
            
            # Wait for disarming confirmation
            timeout = 10
            start_time = time.time()
            while self.vehicle.armed and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
            
            if not self.vehicle.armed:
                return {"success": True, "message": "Vehicle disarmed successfully"}
            else:
                return {"success": False, "error": "Failed to disarm vehicle within timeout"}
                
        except Exception as e:
            return {"success": False, "error": f"Disarming failed: {e}"}
    
    async def _takeoff(self, altitude: float) -> Dict[str, Any]:
        """Take off to specified altitude"""
        try:
            if not self.vehicle.armed:
                arm_result = await self._arm_vehicle()
                if not arm_result["success"]:
                    return arm_result
            
            # Set mode to GUIDED
            mode_result = await self._set_mode("GUIDED")
            if not mode_result["success"]:
                return mode_result
            
            # Take off
            logger.info(f"Taking off to {altitude}m...")
            self.vehicle.simple_takeoff(altitude)
            
            # Wait for takeoff
            timeout = 60
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                current_alt = self.vehicle.location.global_relative_frame.alt
                if current_alt >= altitude * 0.95:  # 95% of target altitude
                    return {"success": True, "message": f"Takeoff completed to {current_alt:.1f}m"}
                await asyncio.sleep(1)
            
            return {"success": False, "error": "Takeoff timeout"}
            
        except Exception as e:
            return {"success": False, "error": f"Takeoff failed: {e}"}
    
    async def _land(self) -> Dict[str, Any]:
        """Land the vehicle"""
        try:
            # Set mode to LAND
            self.vehicle.mode = "LAND"
            
            # Wait for landing
            timeout = 60
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if not self.vehicle.armed:  # Vehicle disarms when landed
                    return {"success": True, "message": "Landing completed"}
                await asyncio.sleep(1)
            
            return {"success": False, "error": "Landing timeout"}
            
        except Exception as e:
            return {"success": False, "error": f"Landing failed: {e}"}
    
    async def _goto_location(self, lat: float, lng: float, alt: float) -> Dict[str, Any]:
        """Go to specified location"""
        try:
            target_location = LocationGlobalRelative(lat, lng, alt)
            self.vehicle.simple_goto(target_location)
            
            return {"success": True, "message": f"Going to location: {lat}, {lng}, {alt}m"}
            
        except Exception as e:
            return {"success": False, "error": f"Goto failed: {e}"}
    
    async def _set_mode(self, mode_name: str) -> Dict[str, Any]:
        """Set vehicle flight mode"""
        try:
            # Get the flight mode
            flight_mode = self.vehicle.mode_mapping.get(mode_name.upper())
            if flight_mode is None:
                available_modes = list(self.vehicle.mode_mapping.keys())
                return {"success": False, "error": f"Invalid mode. Available modes: {available_modes}"}
            
            # Set the mode
            self.vehicle.mode = flight_mode
            
            # Wait for mode change confirmation
            timeout = 10
            start_time = time.time()
            while self.vehicle.mode.name != mode_name.upper() and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
            
            if self.vehicle.mode.name == mode_name.upper():
                return {"success": True, "message": f"Mode set to {mode_name}"}
            else:
                return {"success": False, "error": f"Failed to set mode to {mode_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Mode change failed: {e}"}
    
    async def _return_to_launch(self) -> Dict[str, Any]:
        """Return to launch location"""
        try:
            # Set mode to RTL
            return await self._set_mode("RTL")
            
        except Exception as e:
            return {"success": False, "error": f"RTL failed: {e}"}
    
    def _get_vehicle_status(self) -> Dict[str, Any]:
        """Get comprehensive vehicle status"""
        if not self.vehicle:
            return {"success": False, "error": "Vehicle not connected"}
        
        try:
            location = self.vehicle.location.global_relative_frame
            status = {
                "success": True,
                "drone_id": self.drone_id,
                "connection_status": self.status.value,
                "armed": self.vehicle.armed,
                "armable": self.vehicle.is_armable,
                "mode": self.vehicle.mode.name,
                "system_status": self.vehicle.system_status.state,
                "location": {
                    "lat": float(location.lat) if location else 0,
                    "lng": float(location.lon) if location else 0,
                    "alt": float(location.alt) if location else 0
                },
                "battery": {
                    "voltage": float(self.vehicle.battery.voltage) if self.vehicle.battery else 0,
                    "level": int(self.vehicle.battery.level) if self.vehicle.battery and self.vehicle.battery.level is not None else -1
                },
                "gps": {
                    "fix_type": int(self.vehicle.gps_0.fix_type) if self.vehicle.gps_0 else 0,
                    "satellites": int(self.vehicle.gps_0.satellites_visible) if self.vehicle.gps_0 else 0
                }
            }
            
            return status
            
        except Exception as e:
            return {"success": False, "error": f"Status retrieval failed: {e}"}
    
    def disconnect(self):
        """Disconnect from vehicle"""
        try:
            if self.vehicle:
                self.vehicle.close()
                self.vehicle = None
            
            self._update_status(DroneStatus.DISCONNECTED, "Disconnected from vehicle")
            logger.info(f"Disconnected from drone {self.drone_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def is_connected(self) -> bool:
        """Check if vehicle is connected"""
        if not self.vehicle:
            return False
        
        # Check heartbeat timeout
        if time.time() - self.last_heartbeat > self.heartbeat_timeout:
            logger.warning(f"Heartbeat timeout for drone {self.drone_id}")
            return False
        
        return True
    
    async def check_connection_health(self) -> bool:
        """Check and maintain connection health"""
        if not self.is_connected():
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                
                await asyncio.sleep(self.reconnect_delay)
                return await self.connect_to_vehicle()
            else:
                self._update_status(DroneStatus.ERROR, "Max reconnection attempts reached")
                return False
        
        return True
 