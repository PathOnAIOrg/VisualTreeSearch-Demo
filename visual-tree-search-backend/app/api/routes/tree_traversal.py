import asyncio
import json
from datetime import datetime
import logging
from typing import Dict, Any, List, Set

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
        
        # Send the root node first
        await websocket.send_json({
            "type": "traversal",  # Changed to 'traversal' for consistency with frontend
            "algorithm": "bfs",
            "nodeId": tree_data["id"],
            "nodeName": tree_data["name"],
            "parentId": None,  # Root has no parent
            "isRoot": True,
            "message": f"Root node: {tree_data['name']} (ID: {tree_data['id']})",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Wait to make the traversal visible
        await asyncio.sleep(1)
        
        # Initialize queue with root node's children
        queue = []
        visited = set([tree_data["id"]])
        
        # Add root's children to queue
        if "children" in tree_data and tree_data["children"]:
            for child in tree_data["children"]:
                queue.append((child, tree_data))  # Store child with its parent
                
        # BFS traversal
        while queue:
            # Get the next node and its parent
            child, parent = queue.pop(0)
            
            if child["id"] not in visited:
                visited.add(child["id"])
                
                # Send child node with parent reference
                await websocket.send_json({
                    "type": "traversal",  # Changed to 'traversal' for consistency with frontend
                    "algorithm": "bfs",
                    "nodeId": child["id"],
                    "nodeName": child["name"],
                    "parentId": parent["id"],
                    "isRoot": False,
                    "message": f"Visiting node: {child['name']} (ID: {child['id']}, Parent: {parent['name']})",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Wait to make the traversal visible
                await asyncio.sleep(1)
                
                # Add child's children to queue
                if "children" in child and child["children"]:
                    for grandchild in child["children"]:
                        queue.append((grandchild, child))  # Store child with its parent
        
        # Send completion message
        await websocket.send_json({
            "type": "info",
            "message": "BFS traversal completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except WebSocketDisconnect:
        logging.info("Client disconnected during tree traversal")
    except Exception as e:
        logging.error(f"Error during BFS tree traversal: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error during BFS traversal: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }) 