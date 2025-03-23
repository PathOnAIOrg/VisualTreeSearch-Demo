import asyncio
import json
import websockets
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_WS_URL = "ws://localhost:3000/tree-search-ws"
DEFAULT_STARTING_URL = "http://128.105.145.205:7770/"
DEFAULT_GOAL = "search running shoes, click on the first result"

async def connect_and_test_search(
    ws_url: str,
    starting_url: str,
    goal: str,
    search_algorithm: str = "bfs",
    max_depth: int = 3
):
    """
    Connect to the WebSocket endpoint and test the tree search functionality.
    
    Args:
        ws_url: WebSocket URL to connect to
        starting_url: URL to start the search from
        goal: Goal to achieve
        search_algorithm: Search algorithm to use (bfs or dfs)
        max_depth: Maximum depth for the search tree
    """
    logger.info(f"Connecting to WebSocket at {ws_url}")
    
    async with websockets.connect(ws_url) as websocket:
        logger.info("Connected to WebSocket")
        
        # Wait for connection established message
        response = await websocket.recv()
        data = json.loads(response)
        if data.get("type") == "connection_established":
            logger.info(f"Connection established with ID: {data.get('connection_id')}")
        
        # Send search request
        request = {
            "type": "start_search",
            "agent_type": "SimpleSearchAgent",
            "starting_url": starting_url,
            "goal": goal,
            "search_algorithm": search_algorithm,
            "max_depth": max_depth
        }
        
        logger.info(f"Sending search request: {request}")
        await websocket.send(json.dumps(request))
        
        # Process responses
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                # Log the message type and some key information
                msg_type = data.get("type", "unknown")
                
                if msg_type == "status_update":
                    logger.info(f"Status update: {data.get('status')} - {data.get('message')}")
                
                elif msg_type == "node_update":
                    node_id = data.get("node_id")
                    status = data.get("status")
                    logger.info(f"Node update: {node_id} - {status}")
                    
                    # If node was scored, log the score
                    if status == "scored":
                        logger.info(f"Node score: {data.get('score')}")
                
                elif msg_type == "tree_update":
                    logger.info(f"Tree update received with {len(data.get('nodes', []))} nodes")
                
                elif msg_type == "best_path_update":
                    logger.info(f"Best path update: score={data.get('score')}, path length={len(data.get('path', []))}")
                
                elif msg_type == "search_complete":
                    status = data.get("status")
                    score = data.get("score", "N/A")
                    path_length = len(data.get("path", []))
                    
                    logger.info(f"Search complete: {status}, score={score}, path length={path_length}")
                    logger.info("Path actions:")
                    
                    for i, node in enumerate(data.get("path", [])):
                        logger.info(f"  {i+1}. {node.get('action')}")
                    
                    # Exit the loop when search is complete
                    break
                
                elif msg_type == "error":
                    logger.error(f"Error: {data.get('message')}")
                    break
                
                else:
                    logger.info(f"Received message of type {msg_type}")
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break
    
    logger.info("Test completed")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the tree search WebSocket functionality")
    
    parser.add_argument("--ws-url", type=str, default=DEFAULT_WS_URL,
                        help=f"WebSocket URL (default: {DEFAULT_WS_URL})")
    
    parser.add_argument("--starting-url", type=str, default=DEFAULT_STARTING_URL,
                        help=f"Starting URL for the search (default: {DEFAULT_STARTING_URL})")
    
    parser.add_argument("--goal", type=str, default=DEFAULT_GOAL,
                        help=f"Goal to achieve (default: {DEFAULT_GOAL})")
    
    parser.add_argument("--algorithm", type=str, choices=["bfs", "dfs"], default="bfs",
                        help="Search algorithm to use (default: bfs)")
    
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Maximum depth for the search tree (default: 3)")
    
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    logger.info("Starting tree search WebSocket test")
    logger.info(f"WebSocket URL: {args.ws_url}")
    logger.info(f"Starting URL: {args.starting_url}")
    logger.info(f"Goal: {args.goal}")
    logger.info(f"Algorithm: {args.algorithm}")
    logger.info(f"Max depth: {args.max_depth}")
    
    await connect_and_test_search(
        ws_url=args.ws_url,
        starting_url=args.starting_url,
        goal=args.goal,
        search_algorithm=args.algorithm,
        max_depth=args.max_depth
    )

if __name__ == "__main__":
    asyncio.run(main())
