#!/usr/bin/env python3
"""
ReliefWings Drone Telemetry System - Main Orchestrator
Modular drone telemetry collection and WebSocket communication system
"""

import asyncio
import logging
import time
import signal
import os
from typing import Dict, Any, Optional
from dataclasses import asdict

# Import our modular components
from websocket_client import WebSocketClient
from database import TelemetryDatabase
from drone_controller import DroneController, DroneStatus, TelemetryData
from telemetry_processor import TelemetryProcessor
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/drone_telemetry.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ReliefWingsTelemetrySystem:
    """Main orchestrator for the ReliefWings drone telemetry system"""
    
    def __init__(self, drone_id: str = None, connection_string: str = None):
        # Use config values if not provided
        self.drone_id = drone_id or config.drone.drone_id
        self.connection_string = connection_string or config.drone.connection_string
        self.is_running = False
        
        # Initialize modular components using config
        # self.websocket_client = WebSocketClient(
        #     drone_id=self.drone_id,
        #     websocket_url=config.websocket.server_url,
        #     api_key=config.websocket.api_key
        # )
        
        # self.database = TelemetryDatabase(
        #     db_path=config.database.db_path
        # )
        
        self.drone_controller = DroneController(
            drone_id=self.drone_id,
            connection_string=self.connection_string
        )
        
        self.telemetry_processor = TelemetryProcessor(
            drone_id=self.drone_id
        )
        
        # Setup callbacks between components
        self._setup_callbacks()
        
        # Use config values for timing
        self.telemetry_interval = config.telemetry.collection_interval
        self.last_telemetry_time = 0
        
        # System health monitoring
        self.health_check_interval = config.telemetry.health_check_interval
        self.last_health_check = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_callbacks(self):
        """Setup callbacks between modular components"""
        
        # # WebSocket callbacks
        # self.websocket_client.set_message_callback(self._handle_websocket_message)
        # self.websocket_client.set_connection_callback(self._handle_websocket_status)
        
        # Drone controller callbacks
        self.drone_controller.set_telemetry_callback(self._handle_telemetry_data)
        self.drone_controller.set_status_callback(self._handle_drone_status)
        self.drone_controller.set_command_result_callback(self._handle_command_result)
    
    # def _handle_websocket_message(self, message: Dict[str, Any]):
    #     """Handle messages received from WebSocket"""
    #     try:
    #         message_type = message.get('type')
            
    #         if message_type == 'command':
    #             # Handle drone command
    #             command_id = message.get('id', 0)
    #             command = message.get('command', '')
    #             args = message.get('args', {})
                
    #             logger.info(f"Received command: {command} with args: {args}")
                
    #             # Store command in database
    #             db_command_id = self.database.store_command(self.drone_id, command, args)
                
    #             # Execute command via drone controller
    #             asyncio.create_task(
    #                 self.drone_controller.execute_command(command_id, command, args)
    #             )
                
    #         elif message_type == 'ack':
    #             logger.debug(f"Received acknowledgment: {message}")
                
    #         elif message_type == 'ping':
    #             # Respond to ping
    #             pong_message = {
    #                 'type': 'pong',
    #                 'drone_id': self.drone_id,
    #                 'timestamp': time.time()
    #             }
    #             self.websocket_client.send_message(pong_message)
                
    #     except Exception as e:
    #         logger.error(f"Error handling WebSocket message: {e}")
    
    # def _handle_websocket_status(self, connected: bool, message: str):
    #     """Handle WebSocket connection status changes"""
    #     logger.info(f"WebSocket status: {'connected' if connected else 'disconnected'} - {message}")
        
    #     if connected:
    #         # Send buffered telemetry when connection is restored
    #         asyncio.create_task(self._send_buffered_telemetry())
    

    def _handle_telemetry_data(self, telemetry: TelemetryData):
        """Handle telemetry data from drone controller"""
        try:
            # Convert to dictionary
            telemetry_dict = asdict(telemetry)
            
            # Process telemetry through processor
            processed_telemetry = self.telemetry_processor.process_telemetry(telemetry_dict)
            
            # Store in database
            # self.database.store_telemetry(
            #     self.drone_id,
            #     self.telemetry_processor.format_for_database(processed_telemetry),
            #     telemetry.seq
            # )
            
            # # Send via WebSocket if connected
            # if self.websocket_client.is_connected():
            #     websocket_data = self.telemetry_processor.format_for_websocket(processed_telemetry)
            #     self.websocket_client.send_telemetry(websocket_data)
            
            logger.debug(f"Processed telemetry seq {telemetry.seq}")
            
        except Exception as e:
            logger.error(f"Error handling telemetry data: {e}")
    
    def _handle_drone_status(self, status: DroneStatus, message: str):
        """Handle drone status changes"""
        logger.info(f"Drone status: {status.value} - {message}")
        
        # Log status change to database
        # self.database.log_event(
        #     self.drone_id,
        #     'INFO',
        #     f"Status change: {status.value}",
        #     {'status': status.value, 'message': message}
        # )
        
        # Send status update via WebSocket
        # if self.websocket_client.is_connected():
        #     status_message = {
        #         'type': 'status_update',
        #         'drone_id': self.drone_id,
        #         'status': status.value,
        #         'message': message,
        #         'timestamp': time.time()
        #     }
        #     self.websocket_client.send_message(status_message)
    
    def _handle_command_result(self, command_id: int, status: str, result: Dict[str, Any]):
        """Handle command execution results"""
        logger.info(f"Command {command_id} {status}: {result}")
        
        # Update command status in database
        # self.database.update_command_status(command_id, status, result)
        
        # Send result via WebSocket
        # if self.websocket_client.is_connected():
        #     result_message = {
        #         'type': 'command_result',
        #         'command_id': command_id,
        #         'status': status,
        #         'result': result,
        #         'drone_id': self.drone_id,
        #         'timestamp': time.time()
        #     }
        #     self.websocket_client.send_message(result_message)
    
    # async def _send_buffered_telemetry(self):
        # """Send any buffered telemetry data"""
        # try:
            # Get unsent telemetry from database
            # unsent_telemetry = self.database.get_unsent_telemetry(limit=50)
            
            # if unsent_telemetry:
            #     sent_ids = []
                
            #     for telemetry_record in unsent_telemetry:
            #         # Format for WebSocket
            #         websocket_data = self.telemetry_processor.format_for_websocket(telemetry_record['data'])
                    
            #         if self.websocket_client.send_telemetry(websocket_data):
            #             sent_ids.append(telemetry_record['id'])
                        
            #             # Small delay to avoid overwhelming the connection
            #             await asyncio.sleep(0.1)
                
                # Mark sent telemetry as sent in database
                # if sent_ids:
                #     self.database.mark_telemetry_sent(sent_ids)
                #     logger.info(f"Sent {len(sent_ids)} buffered telemetry records")
                    
        # except Exception as e:
        #     logger.error(f"Error sending buffered telemetry: {e}")
    
    async def _health_check(self):
        """Perform system health checks"""
        try:
            current_time = time.time()
            
            if current_time - self.last_health_check < self.health_check_interval:
                return
            
            self.last_health_check = current_time
            
            # Check drone connection health
            drone_healthy = await self.drone_controller.check_connection_health()
            
            # Check WebSocket connection health
            # websocket_healthy = self.websocket_client.is_connected()
            
            # Get database statistics
            # db_stats = self.database.get_database_stats()
            
            # Get processor metrics
            processor_metrics = self.telemetry_processor.get_health_metrics()
            
            # Compile health report
            health_report = {
                'drone_id': self.drone_id,
                'timestamp': current_time,
                'components': {
                    'drone_controller': {
                        'healthy': drone_healthy,
                        'status': self.drone_controller.status.value
                    },
                    # 'websocket_client': {
                    #     'healthy': websocket_healthy,
                    #     'connected': websocket_healthy
                    # },
                    # 'database': {
                    #     'healthy': True,  # Database is always considered healthy if we can query it
                    #     'stats': db_stats
                    # },
                    'telemetry_processor': {
                        'healthy': processor_metrics['status'] == 'healthy',
                        'metrics': processor_metrics
                    }
                },
                # 'system_health': all([drone_healthy, websocket_healthy])
            }

            logger.info(f"System health: {'HEALTHY' if health_report['system_health'] else 'DEGRADED'}")

            # Log health report to databaseket.server_url}")
        # logger.info(f"Database: {config.database.db_path}")
            # self.database.log_event(
            #     self.drone_id,
            #     'INFO' if health_report['system_healthy'] else 'WARNING',
            #     'System health check',
            #     health_report
            # )
            
            # Send health report via WebSocket
            # if websocket_healthy:
            #     health_message = {
            #         'type': 'health_report',
            #         'data': health_report
            #     }
            #     self.websocket_client.send_message(health_message)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _telemetry_loop(self):
        """Main telemetry collection loop"""
        logger.info("Starting telemetry loop...")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Check if it's time for telemetry collection
                if current_time - self.last_telemetry_time >= self.telemetry_interval:
                    # Get telemetry data from drone controller
                    telemetry_data = self.drone_controller.get_telemetry_data()
                    
                    if telemetry_data:
                        # The telemetry is handled automatically via the callback
                        self.last_telemetry_time = current_time
                
                # Perform health checks
                await self._health_check()
                
                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Telemetry loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Periodic cleanup tasks"""
        while self.is_running:
            try:
                # Wait 1 hour between cleanups
                await asyncio.sleep(3600)
                
                # Clean up old database entries
                # self.database.cleanup_old_data(days=7)
                
                logger.info("Performed periodic cleanup")
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("Shutting down telemetry system...")
        
        self.is_running = False
        
        # Close WebSocket connection
        # await self.websocket_client.disconnect()
        
        # Disconnect from drone
        self.drone_controller.disconnect()
        
        logger.info("Shutdown complete")
    
    async def run(self):
        """Main run method"""
        logger.info(f"Starting ReliefWings Telemetry System for drone {self.drone_id}")
        self.is_running = True
        
        try:
            # Connect to drone
            logger.info("Connecting to drone...")
            if not await self.drone_controller.connect_to_vehicle():
                logger.error("Failed to connect to drone, exiting...")
                return
            
            # Connect to WebSocket server
            # logger.info("Connecting to WebSocket server...")
            # await self.websocket_client.connect()
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self._telemetry_loop(), name="telemetry_loop"),
                asyncio.create_task(self._cleanup_loop(), name="cleanup_loop")
            ]
            
            logger.info("All systems started successfully")
            
            # Wait for all tasks to complete (or be cancelled)
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            await self.shutdown()

async def main():
    """Main entry point"""
    try:
        # Validate configuration on startup
        logger.info("Validating system configuration...")
        validation = config.validate_config()
        if not validation['valid']:
            logger.error("Configuration issues found:")
            for issue in validation['issues']:
                logger.error(f"  - {issue}")
            raise SystemExit("Configuration validation failed")
        
        if validation['warnings']:
            logger.warning("Configuration warnings:")
            for warning in validation['warnings']:
                logger.warning(f"  - {warning}")
        
        # Check environment setup
        env_info = config.get_environment_info()
        if env_info['using_defaults']:
            logger.info(f"Using default values for: {', '.join(env_info['using_defaults'])}")
        
        # Configuration
        drone_id = config.drone.drone_id
        connection_string = config.drone.connection_string
        
        logger.info(f"Initializing ReliefWings telemetry system...")
        logger.info(f"Drone ID: {drone_id}")
        logger.info(f"Connection: {connection_string}")
        # logger.info(f"WebSocket URL: {config.websocket.server_url}")
        # logger.info(f"Database: {config.database.db_path}")
        
        # Create and run system
        system = ReliefWingsTelemetrySystem(
            drone_id=drone_id,
            connection_string=connection_string
        )
        
        # Run the system
        await system.run()
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
