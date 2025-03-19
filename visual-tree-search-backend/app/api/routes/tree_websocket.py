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

# Import the tree traversal handler
from app.api.routes.tree_traversal import bfs_traversal

router = APIRouter()

# Track active WebSocket connections for tree visualization
active_tree_connections: List[WebSocket] = []

# Track the ping task
tree_ping_task = None

async def send_to_all_tree_clients(data: Dict[str, Any]):
    """Send a message to all connected tree visualization clients"""
    message = json.dumps(data)
    for connection in active_tree_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logging.error(f"Error sending message to tree client: {e}")

async def ping_tree_clients():
    """Send a ping to all tree visualization clients every second"""
    while True:
        if active_tree_connections:
            data = {
                "type": "ping",
                "message": "Tree server heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_to_all_tree_clients(data)
            logging.info(f"Sent ping to {len(active_tree_connections)} tree websocket clients")
        await asyncio.sleep(1)

# Define the WebSocket endpoint for tree visualization
async def tree_websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for tree visualization"""
    await websocket.accept()
    active_tree_connections.append(websocket)
    
    # Start ping task if not already running
    global tree_ping_task
    if tree_ping_task is None or tree_ping_task.done():
        tree_ping_task = asyncio.create_task(ping_tree_clients())
    
    logging.info(f"Tree WebSocket client connected - total clients: {len(active_tree_connections)}")
    
    # Send initial connection message
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to Tree WebSocket server"
    })
    
    try:
        while True:
            # Receive message from the client
            data = await websocket.receive_text()
            
            try:
                # Parse the message
                parsed_data = json.loads(data)
                logging.info(f"Received tree message: {parsed_data}")
                
                # Handle tree data
                if parsed_data.get("type") == "tree" and "content" in parsed_data:
                    tree_data = parsed_data["content"]
                    
                    # Log the received tree
                    logging.info(f"Received tree data: {json.dumps(tree_data)[:100]}...")
                    
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "info",
                        "message": "Tree data received",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Start BFS traversal
                    await bfs_traversal(websocket, tree_data)
                else:
                    # Echo back other message types
                    await websocket.send_json({
                        "type": "echo",
                        "message": parsed_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing tree message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}"
                })
    except WebSocketDisconnect:
        # Remove connection when client disconnects
        if websocket in active_tree_connections:
            active_tree_connections.remove(websocket)
        logging.info(f"Tree WebSocket client disconnected - remaining clients: {len(active_tree_connections)}")
    except Exception as e:
        logging.error(f"Tree WebSocket error: {e}")
        if websocket in active_tree_connections:
            active_tree_connections.remove(websocket)

# Add a route for testing Tree WebSocket functionality via HTTP
@router.get("/status")
async def tree_websocket_status():
    """Get Tree WebSocket connection status"""
    return {
        "active": len(active_tree_connections),
        "status": "running"
    } 