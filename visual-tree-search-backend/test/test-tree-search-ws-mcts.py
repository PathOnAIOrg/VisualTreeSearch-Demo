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
DEFAULT_WS_URL = "ws://localhost:3000/new-tree-search-ws"
DEFAULT_STARTING_URL = "http://xwebarena.pathonai.org:7770/"
DEFAULT_GOAL = "search running shoes, click on the first result"

async def connect_and_test_search(
    ws_url: str,
    starting_url: str,
    goal: str,
    search_algorithm: str = "bfs",
    max_depth: int = 3,    
    max_iterations: int = 3
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
            "agent_type": "MCTSAgent",
            "starting_url": starting_url,
            "goal": goal,
            "search_algorithm": search_algorithm,
            "max_depth": max_depth,
            "max_iterations": max_iterations 
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
                
                elif msg_type == "browser_setup":
                    logger.info(f"Browser setup: {data.get('status')}")
                    if data.get('live_browser_url'):
                        logger.info(f"Live browser URL: {data.get('live_browser_url')}")
                        
                elif msg_type == "iteration_start":
                    logger.info(f"Iteration start: {data.get('iteration')}")

                elif msg_type == "step_start":
                    logger.info(f"Step start: {data.get('step')} - {data.get('step_name')}")
                
                elif msg_type == "node_update":
                    node_id = data.get("node_id")
                    status = data.get("status")
                    logger.info(f"Node update: {node_id} - {status}")
                    
                    # If node was scored, log the score
                    if status == "scored":
                        logger.info(f"Node score: {data.get('score')}")
                
                elif msg_type == "trajectory_update":
                    logger.info(f"Trajectory update received with {data.get('trajectory')}")
                
                elif msg_type == "tree_update":
                    logger.info(f"Tree update received with {data.get('tree')}")
                
                elif msg_type == "best_path_update":
                    logger.info(f"Best path update: score={data.get('score')}, path length={len(data.get('path', []))}")
                
                elif msg_type == "search_complete":
                    status = data.get("status")
                    score = data.get("score", "N/A")
                    path = data.get("path", [])
                    path_length = len(path)
                    
                    logger.info(f"Search complete: {status}, score={score}, path length={path_length}")
                    if path_length > 0:
                        logger.info("Path actions:")
                        for i, node in enumerate(path):
                            # Extract action and add fallback if missing
                            action = node.get('action', 'unknown_action')
                            logger.info(f"  {i+1}. {action}")
                    else:
                        logger.info("No path was returned - search failed to find a valid solution")
                        
                        # Add diagnostic info about why the search might have failed
                        if status == "failure":
                            reason = data.get("message", "No reason provided")
                            logger.info(f"Failure reason: {reason}")
                        
                        # Check for any fallback actions in the response
                        fallback = data.get("fallback_action")
                        if fallback:
                            logger.info(f"Fallback action provided: {fallback}")                
                    
                    # Exit the loop when search is complete
                    break
                
                elif msg_type == "error":
                    logger.error(f"Error: {data.get('message')}")
                    break
                
                else:
                    logger.info(f"Received message of type {msg_type}")
                    logger.info(f"Message: {data}")
                    
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
    
    parser.add_argument("--algorithm", type=str, choices=["bfs", "dfs", "lats", "mcts"], default="mcts",
                        help="Search algorithm to use (default: mcts)")
    
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Maximum depth for the search tree (default: 3)")
    parser.add_argument("--max-iterations", type=int, default=3,
                        help="Maximum number of MCTS iterations (default: 3)")
    
    
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
    logger.info(f"Max iterations: {args.max_iterations}")
    
    await connect_and_test_search(
        ws_url=args.ws_url,
        starting_url=args.starting_url,
        goal=args.goal,
        search_algorithm=args.algorithm,
        max_depth=args.max_depth,
        max_iterations=args.max_iterations
    )

if __name__ == "__main__":
    asyncio.run(main())