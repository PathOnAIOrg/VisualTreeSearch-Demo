import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Track active WebSocket connections
active_connections: List[WebSocket] = []

# Track the ping task
ping_task = None

async def send_to_all(data: Dict[str, Any]):
    """Send a message to all connected clients"""
    message = json.dumps(data)
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

async def ping_clients():
    """Send a ping to all clients every second"""
    while True:
        if active_connections:
            data = {
                "type": "ping",
                "message": "Server heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_to_all(data)
            logging.info(f"Sent ping to {len(active_connections)} websocket clients")
        await asyncio.sleep(1)

# Define the WebSocket endpoint that will be used in main.py
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    await websocket.accept()
    active_connections.append(websocket)
    
    # Start ping task if not already running
    global ping_task
    if ping_task is None or ping_task.done():
        ping_task = asyncio.create_task(ping_clients())
    
    logging.info(f"WebSocket client connected - total clients: {len(active_connections)}")
    
    # Send initial connection message
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to WebSocket server"
    })
    
    try:
        while True:
            # Receive message from the client
            data = await websocket.receive_text()
            
            try:
                # Parse the message
                parsed_data = json.loads(data)
                logging.info(f"Received message: {parsed_data}")
                
                # Echo back the message
                await websocket.send_json({
                    "type": "echo",
                    "message": parsed_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}"
                })
    except WebSocketDisconnect:
        # Remove connection when client disconnects
        if websocket in active_connections:
            active_connections.remove(websocket)
        logging.info(f"WebSocket client disconnected - remaining clients: {len(active_connections)}")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# Add a route for testing WebSocket functionality via HTTP
@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active": len(active_connections),
        "status": "running"
    }