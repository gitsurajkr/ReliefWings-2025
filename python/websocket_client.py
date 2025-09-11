#!/usr/bin/env python3
"""
WebSocket Client Module for ReliefWings Drone Telemetry System
Handles WebSocket connections and communication with the backend server
"""

import websocket
import json
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class WebSocketClient:
    """WebSocket client for communicating with the backend server"""
    
    def __init__(self, 
                 websocket_url: str = "ws://localhost:8081",
                 drone_id: str = "drone-01",
                 api_key: str = None):
        self.websocket_url = websocket_url
        self.drone_id = drone_id
        self.api_key = api_key
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        self.callbacks = {
            'on_message': None,
            'on_connected': None,
            'on_disconnected': None,
            'on_error': None
        }
        
    def set_callback(self, event: str, callback: Callable):
        """Set callback functions for WebSocket events"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            logger.warning(f"Unknown callback event: {event}")
    
    def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            logger.info(f"Connecting to WebSocket server: {self.websocket_url}")
            
            # WebSocket URL with authentication
            auth_params = f"?drone_id={self.drone_id}"
            if self.api_key:
                auth_params += f"&api_key={self.api_key}"
            
            full_url = f"{self.websocket_url}{auth_params}"
            
            self.ws = websocket.WebSocketApp(
                full_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Start WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()
            
            # Wait for connection with timeout
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("WebSocket connected successfully")
                self.reconnect_attempts = 0
                return True
            else:
                logger.error("WebSocket connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            self.ws.close()
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def send_telemetry(self, telemetry_data: Dict[str, Any]) -> bool:
        """Send telemetry data to server"""
        try:
            if not self.connected or not self.ws:
                logger.warning("WebSocket not connected, cannot send telemetry")
                return False
            
            message = {
                "type": "telemetry",
                "data": telemetry_data,
                "timestamp": int(time.time() * 1000)
            }
            
            self.ws.send(json.dumps(message))
            logger.debug(f"Sent telemetry for drone {telemetry_data.get('drone_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send telemetry: {e}")
            return False
    
    def send_command_ack(self, command: str, status: str, result: Any = None) -> bool:
        """Send command acknowledgment to server"""
        try:
            if not self.connected or not self.ws:
                logger.warning("WebSocket not connected, cannot send command ack")
                return False
            
            message = {
                "type": "command_ack",
                "data": {
                    "drone_id": self.drone_id,
                    "command": command,
                    "status": status,
                    "result": result,
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            self.ws.send(json.dumps(message))
            logger.info(f"Sent command acknowledgment: {command} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command ack: {e}")
            return False
    
    def _on_open(self, ws):
        """WebSocket connection opened"""
        self.connected = True
        logger.info(f"WebSocket connected to {self.websocket_url}")
        
        # Send initial connection message
        init_message = {
            "type": "drone_connect",
            "data": {
                "drone_id": self.drone_id,
                "client_type": "pi",
                "timestamp": int(time.time() * 1000)
            }
        }
        ws.send(json.dumps(init_message))
        
        if self.callbacks['on_connected']:
            self.callbacks['on_connected']()
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            logger.debug(f"Received message: {data}")
            
            if self.callbacks['on_message']:
                self.callbacks['on_message'](data)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        self.connected = False
        
        if self.callbacks['on_error']:
            self.callbacks['on_error'](error)
        
        # Attempt reconnection
        self._attempt_reconnect()
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        self.connected = False
        logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        if self.callbacks['on_disconnected']:
            self.callbacks['on_disconnected']()
        
        # Attempt reconnection if not intentionally closed
        if close_status_code != 1000:  # 1000 = normal closure
            self._attempt_reconnect()
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to WebSocket server"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, giving up")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts}) in {self.reconnect_interval} seconds...")
        
        time.sleep(self.reconnect_interval)
        
        # Exponential backoff
        self.reconnect_interval = min(self.reconnect_interval * 2, 60)
        
        # Attempt reconnection
        threading.Thread(target=self.connect, daemon=True).start()
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.connected,
            "url": self.websocket_url,
            "drone_id": self.drone_id,
            "reconnect_attempts": self.reconnect_attempts,
            "reconnect_interval": self.reconnect_interval
        }
