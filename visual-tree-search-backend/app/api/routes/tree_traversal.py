import asyncio
import json
from datetime import datetime
import logging
from typing import Dict, Any, List

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import WebSocket, WebSocketDisconnect

# Define a function to perform BFS traversal of the tree
async def bfs_traversal(websocket: WebSocket, tree_data: Dict[str, Any]):
    """Perform BFS traversal of the tree and send updates to the client"""
    try:
        # Send acknowledgment
        await websocket.send_json({
            "type": "info",
            "message": "Starting BFS traversal",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Initialize queue with root node
        queue = [tree_data]
        
        # BFS traversal
        while queue:
            # Get the next node
            node = queue.pop(0)
            
            # Send current node to client
            await websocket.send_json({
                "type": "traversal",
                "nodeId": node["id"],
                "nodeName": node["name"],
                "message": f"Visiting node: {node['name']} (ID: {node['id']})",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Add children to queue
            if "children" in node and node["children"]:
                for child in node["children"]:
                    queue.append(child)
            
            # Pause to make the traversal visible
            await asyncio.sleep(1)
        
        # Send completion message
        await websocket.send_json({
            "type": "info",
            "message": "BFS traversal completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except WebSocketDisconnect:
        logging.info("Client disconnected during tree traversal")
    except Exception as e:
        logging.error(f"Error during tree traversal: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error during traversal: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }) 