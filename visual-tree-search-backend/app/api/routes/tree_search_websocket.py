import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Set
import logging
from collections import deque

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Import necessary components for the search agent
from ..lwats.webagent_utils_async.utils.playwright_manager import setup_playwright
from ..lwats.core_async.config import AgentConfig
from ..lwats.core_async.agent_factory import setup_search_agent
from ..lwats.agents_async.SimpleSearchAgents.tree_vis import collect_all_nodes
from ..lwats.agents_async.SimpleSearchAgents.trajectory_score import create_llm_prompt, score_trajectory_with_openai

router = APIRouter()

# Track active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# This is the function that will be called from main.py
async def tree_search_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for tree search visualization and control"""
    await websocket.accept()
    connection_id = str(id(websocket))
    active_connections[connection_id] = websocket
    
    logging.info(f"WebSocket connection established with ID: {connection_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for messages from the client
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "ping":
                await websocket.send_json({
                    "type": "pong", 
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message["type"] == "start_search":
                # Start the search process
                await handle_search_request(websocket, message)
                
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected with ID: {connection_id}")
    except Exception as e:
        logging.error(f"Error in WebSocket connection: {e}")
    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]

async def handle_search_request(websocket: WebSocket, message: Dict[str, Any]):
    """Handle a search request from the client"""
    try:
        # Extract parameters from the message
        agent_type = message.get("agent_type", "SimpleSearchAgent")
        starting_url = message.get("starting_url", "http://128.105.145.205:7770/")
        goal = message.get("goal", "search running shoes, click on the first result")
        search_algorithm = message.get("search_algorithm", "bfs")
        max_depth = message.get("max_depth", 3)
        storage_state = message.get("storage_state", "app/api/shopping.json")
        
        # Send status update
        await websocket.send_json({
            "type": "status_update",
            "status": "initializing",
            "message": "Initializing search agent",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Create agent configuration
        config = AgentConfig(
            search_algorithm=search_algorithm,
            max_depth=max_depth,
            storage_state=storage_state,
            headless=False
        )
        
        # Send status update
        await websocket.send_json({
            "type": "status_update",
            "status": "setting_up",
            "message": "Setting up playwright browser",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Setup playwright and agent
        agent, playwright_manager = await setup_search_agent(
            agent_type=agent_type,
            starting_url=starting_url,
            goal=goal,
            images=[],  # No initial images
            agent_config=config
        )
        
        # Send status update
        await websocket.send_json({
            "type": "status_update",
            "status": "running",
            "message": "Search agent initialized, starting search",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Run search with WebSocket updates
        if search_algorithm.lower() == "bfs":
            # Use the agent's built-in WebSocket-enabled BFS method
            await agent.bfs_with_websocket(websocket)
        elif search_algorithm.lower() == "dfs":
            # Use the agent's built-in WebSocket-enabled DFS method
            await agent.dfs_with_websocket(websocket)
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unsupported algorithm: {search_algorithm}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Clean up
        await playwright_manager.close()
        
    except Exception as e:
        logging.error(f"Error handling search request: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error during search: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        })

async def send_tree_update(websocket: WebSocket, root_node):
    """Send a tree update to the client"""
    try:
        # Collect all nodes in the tree
        nodes = collect_all_nodes(root_node)
        
        # Convert nodes to a format suitable for visualization
        tree_data = []
        for node in nodes:
            node_data = {
                "id": id(node),
                "parent_id": id(node.parent) if node.parent else None,
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description,
                "depth": node.depth,
                "is_terminal": node.is_terminal,
                "score": getattr(node, "value", 0) / getattr(node, "visits", 1) if hasattr(node, "visits") and node.visits > 0 else 0
            }
            tree_data.append(node_data)
        
        await websocket.send_json({
            "type": "tree_update",
            "nodes": tree_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Error sending tree update: {e}")

async def send_trajectory_update(websocket: WebSocket, node, status: str):
    """Send a trajectory update to the client"""
    try:
        # Get path from root to this node
        path = []
        current = node
        while current:
            path.append(current)
            current = current.parent
        path = list(reversed(path))
        
        # Convert path to a format suitable for visualization
        trajectory_data = []
        for i, node in enumerate(path):
            if i == 0:  # Skip root node in display
                continue
                
            node_data = {
                "id": id(node),
                "action": node.action,
                "description": node.natural_language_description,
                "feedback": node.feedback if hasattr(node, "feedback") else None,
                "depth": node.depth
            }
            trajectory_data.append(node_data)
        
        await websocket.send_json({
            "type": f"trajectory_{status}",  # trajectory_start or trajectory_complete
            "trajectory": trajectory_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Error sending trajectory update: {e}")

# Add a route for testing WebSocket status via HTTP
@router.get("/status")
async def tree_search_websocket_status():
    """Get Tree Search WebSocket connection status"""
    return {
        "active_connections": len(active_connections),
        "status": "running"
    }