"""
Bluefin WebSocket Manager

This module provides a WebSocket manager for the Bluefin Exchange API,
allowing real-time data streaming for market data, order updates, and more.

Usage:
    from core.bluefin_api.websocket import BluefinWebSocketManager
    
    # Create a WebSocket manager
    ws_manager = BluefinWebSocketManager()
    
    # Connect and subscribe to streams
    await ws_manager.connect()
    await ws_manager.subscribe(["btcperp@trade", "btcperp@kline_1m"])
    
    # Process messages
    async for message in ws_manager.messages():
        print(f"Received: {message}")
    
    # Unsubscribe and disconnect
    await ws_manager.unsubscribe(["btcperp@trade"])
    await ws_manager.disconnect()
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable, Union

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = Any  # Type placeholder

# Default WebSocket URL
DEFAULT_WS_URL = "wss://dstream.api.sui-prod.bluefin.io/ws"

logger = logging.getLogger(__name__)


class BluefinWebSocketManager:
    """
    WebSocket manager for Bluefin Exchange.
    
    This class manages WebSocket connections to Bluefin Exchange,
    handling subscriptions, message processing, and reconnection.
    """
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize the WebSocket manager.
        
        Args:
            url: WebSocket URL (defaults to environment variable or default URL)
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package is required for WebSocket functionality")
        
        self.url = url or os.getenv("BLUEFIN_WS_URL", DEFAULT_WS_URL)
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.subscribed_streams: List[str] = []
        self.running = False
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.reconnect_interval = 5  # seconds
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        self.last_message_time = 0
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> bool:
        """
        Connect to the WebSocket endpoint.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.websocket and self.websocket.open:
            logger.info("WebSocket already connected")
            return True
        
        try:
            logger.info(f"Connecting to WebSocket at {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.running = True
            self.reconnect_attempts = 0
            self.last_message_time = time.time()
            
            # Start message processor
            asyncio.create_task(self._process_messages())
            
            # Start heartbeat
            self._start_heartbeat()
            
            logger.info("WebSocket connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket endpoint."""
        self.running = False
        
        # Stop heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        logger.info("WebSocket disconnected")
    
    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to the WebSocket.
        
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Maximum reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        # Close existing connection if any
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Wait before reconnecting
        await asyncio.sleep(self.reconnect_interval)
        
        # Try to connect
        connected = await self.connect()
        
        # If connected, resubscribe to streams
        if connected and self.subscribed_streams:
            await self.subscribe(self.subscribed_streams)
        
        return connected
    
    async def subscribe(self, streams: Union[str, List[str]]) -> bool:
        """
        Subscribe to one or more streams.
        
        Args:
            streams: Stream name(s) to subscribe to (e.g., "btcperp@trade")
        
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if not self.websocket or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        if isinstance(streams, str):
            streams = [streams]
        
        try:
            # Create subscription message
            message = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": int(time.time())
            }
            
            # Send subscription request
            await self.websocket.send(json.dumps(message))
            logger.info(f"Subscription request sent for streams: {', '.join(streams)}")
            
            # Wait for subscription response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            # Check for successful subscription
            if "result" in response_data and response_data["result"] is None:
                logger.info(f"Successfully subscribed to streams: {', '.join(streams)}")
                self.subscribed_streams.extend(streams)
                return True
            else:
                logger.error(f"Subscription failed: {response_data}")
                return False
        except Exception as e:
            logger.error(f"Error during subscription: {str(e)}")
            return False
    
    async def unsubscribe(self, streams: Union[str, List[str]]) -> bool:
        """
        Unsubscribe from one or more streams.
        
        Args:
            streams: Stream name(s) to unsubscribe from
        
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        if not self.websocket or not self.running:
            logger.error("WebSocket not connected")
            return False
        
        if isinstance(streams, str):
            streams = [streams]
        
        try:
            # Create unsubscription message
            message = {
                "method": "UNSUBSCRIBE",
                "params": streams,
                "id": int(time.time())
            }
            
            # Send unsubscription request
            await self.websocket.send(json.dumps(message))
            logger.info(f"Unsubscription request sent for streams: {', '.join(streams)}")
            
            # Wait for unsubscription response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            # Check for successful unsubscription
            if "result" in response_data and response_data["result"] is None:
                logger.info(f"Successfully unsubscribed from streams: {', '.join(streams)}")
                for stream in streams:
                    if stream in self.subscribed_streams:
                        self.subscribed_streams.remove(stream)
                return True
            else:
                logger.error(f"Unsubscription failed: {response_data}")
                return False
        except Exception as e:
            logger.error(f"Error during unsubscription: {str(e)}")
            return False
    
    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages."""
        if not self.websocket:
            return
        
        while self.running:
            try:
                # Receive message
                message = await self.websocket.recv()
                self.last_message_time = time.time()
                
                # Parse message
                data = json.loads(message)
                
                # Add to queue
                await self.message_queue.put(data)
                
                # Trigger event handlers
                await self._trigger_event_handlers(data)
            except asyncio.CancelledError:
                # Task was cancelled
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                
                # Attempt to reconnect
                if self.running:
                    reconnected = await self.reconnect()
                    if not reconnected:
                        break
    
    async def messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generator for consuming messages from the queue.
        
        Yields:
            Dict[str, Any]: WebSocket message
        """
        while self.running:
            try:
                message = await self.message_queue.get()
                yield message
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
    
    def _start_heartbeat(self) -> None:
        """Start the heartbeat task to keep the connection alive."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop to check connection health and reconnect if needed."""
        while self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check if we've received a message recently
                if time.time() - self.last_message_time > self.heartbeat_interval * 2:
                    logger.warning("No messages received recently, reconnecting...")
                    await self.reconnect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
    
    def on(self, event_type: str, callback: Callable) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Event type to listen for (e.g., "trade", "kline")
            callback: Callback function to call when event is received
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(callback)
        logger.info(f"Registered event handler for {event_type}")
    
    async def _trigger_event_handlers(self, data: Dict[str, Any]) -> None:
        """
        Trigger event handlers for a message.
        
        Args:
            data: WebSocket message data
        """
        # Check if message has an event type
        event_type = data.get("e")
        
        if event_type and event_type in self.event_handlers:
            for callback in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {str(e)}")


async def example():
    """Example usage of the BluefinWebSocketManager."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create WebSocket manager
    ws_manager = BluefinWebSocketManager()
    
    try:
        # Connect to WebSocket
        connected = await ws_manager.connect()
        if not connected:
            logger.error("Failed to connect to WebSocket")
            return
        
        # Subscribe to streams
        streams = ["btcperp@trade", "btcperp@kline_1m"]
        subscribed = await ws_manager.subscribe(streams)
        if not subscribed:
            logger.error("Failed to subscribe to streams")
            return
        
        # Process messages for 30 seconds
        end_time = time.time() + 30
        async for message in ws_manager.messages():
            logger.info(f"Received message: {message}")
            
            if time.time() > end_time:
                break
        
        # Unsubscribe from streams
        await ws_manager.unsubscribe(streams)
    finally:
        # Disconnect
        await ws_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(example()) 