import asyncio
import json
import websockets
import argparse
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# account_reset
# browser_setup

## for LATS
# step_start
# node_created
# node_selected
# node_selected_for_simulation
# tree_update_node_expansion
# tree_update_node_children_evaluation
# tree_update_node_backpropagation
# removed_simulation

COLORS = {
    # Core updates
    'iteration_start': '\033[94m',    # Blue
    'step_start': '\033[94m',         # Blue
    
    # Node operations
    'node_selected': '\033[92m',      # Green
    'node_selected_for_simulation': '\033[92m',      # Green
    'node_created': '\033[92m',       # Green
    'node_simulated': '\033[92m',     # Green
    'node_terminal': '\033[92m',      # Green
    
    # Tree/Path updates
    'tree_update': '\033[96m',        # Cyan
    'tree_update_node_selection': '\033[96m', # Cyan
    'tree_update_node_expansion': '\033[96m',  # Cyan
    'tree_update_node_evaluation': '\033[96m', # Cyan
    'tree_update_node_children_evaluation': '\033[96m', # Cyan
    'tree_update_node_backpropagation': '\033[96m', # Cyan
    'tree_update_simulation': '\033[96m', # Cyan
    'trajectory_update': '\033[96m',   # Cyan
    'removed_simulation': '\033[96m',  # Cyan
    
    # Results/Completion
    'simulation_result': '\033[93m',   # Yellow
    'search_complete': '\033[95m',     # Magenta
    'success': '\033[95m',            # Magenta
    'partial_success': '\033[93m',     # Yellow
    'failure': '\033[91m',            # Red
    
    # System messages
    'account_reset': '\033[91m',       # Red
    'browser_setup': '\033[91m',       # Red
    'error': '\033[91m',              # Red
    
    # Status updates
    'status_update': '\033[94m',      # Blue
    'reset': '\033[0m'                # Reset
}

# Default values
DEFAULT_WS_URL = "ws://localhost:3000/tree-search-ws"
DEFAULT_STARTING_URL = "http://xwebarena.pathonai.org:7770/"
DEFAULT_GOAL = "search running shoes, click on the first result"

async def connect_and_test_search(
    ws_url: str,
    starting_url: str,
    goal: str,
    search_algorithm: str = "bfs",
    max_depth: int = 3,
    iterations: int = 5
):
    """
    Connect to the WebSocket endpoint and test the tree search functionality.
    
    Args:
        ws_url: WebSocket URL to connect to
        starting_url: URL to start the search from
        goal: Goal to achieve
        search_algorithm: Search algorithm to use (bfs or dfs)
        max_depth: Maximum depth for the search tree
        iterations: Number of iterations for MCTS algorithm
    """
    logger.info(f"Connecting to WebSocket at {ws_url}")
    
    async with websockets.connect(ws_url) as websocket:
        logger.info("Connected to WebSocket")
        
        # Wait for connection established message
        response = await websocket.recv()
        data = json.loads(response)
        if data.get("type") == "connection_established":
            logger.info(f"Connection established with ID: {data.get('connection_id')}")
        if search_algorithm in ["bfs", "dfs"]:
            agent_type = "SimpleSearchAgent"
        elif search_algorithm in ["lats"]:
            agent_type = "LATSAgent"
        elif search_algorithm in ["mcts"]:
            agent_type = "MCTSAgent"
        else:
            raise ValueError(f"Invalid search algorithm: {search_algorithm}")
        # Send search request
        request = {
            "type": "start_search",
            "agent_type": agent_type,
            "starting_url": starting_url,
            "goal": goal,
            "search_algorithm": search_algorithm,
            "max_depth": max_depth,
            "iterations": iterations
        }
        
        logger.info(f"Sending search request: {request}")
        await websocket.send(json.dumps(request))
        
        # Process responses
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                # Print the raw websocket message with colored type
                msg_type = data.get("type", "unknown")
                color = COLORS.get(msg_type, COLORS['reset'])
                print(f"\nWebSocket message - Type: {color}{msg_type}{COLORS['reset']}")
                print(f"Raw message: {json.dumps(data, indent=2)}")

                if msg_type == "search_complete":
                    break
                    
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
    
    parser.add_argument("--iterations", type=int, default=5,
                        help="Number of iterations for LATS algorithm (default: 5)")
    
    # Add the new argument for log file
    parser.add_argument("--log-file", type=str, 
                        help="File to save the colored output to")
    
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging to file if requested
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_file = None
    
    if args.log_file:
        class TeeOutput:
            def __init__(self, terminal, log_file):
                self.terminal = terminal
                self.log_file = log_file
                
            def write(self, message):
                self.terminal.write(message)
                self.log_file.write(message)
                
            def flush(self):
                self.terminal.flush()
                self.log_file.flush()
        
        log_file = open(args.log_file, 'w', encoding='utf-8')
        sys.stdout = TeeOutput(sys.stdout, log_file)
        sys.stderr = TeeOutput(sys.stderr, log_file)
        logger.info(f"Logging colored output to {args.log_file}")
    
    logger.info("Starting tree search WebSocket test")
    logger.info(f"WebSocket URL: {args.ws_url}")
    logger.info(f"Starting URL: {args.starting_url}")
    logger.info(f"Goal: {args.goal}")
    logger.info(f"Algorithm: {args.algorithm}")
    logger.info(f"Max depth: {args.max_depth}")
    logger.info(f"Iterations: {args.iterations}")
    
    try:
        await connect_and_test_search(
            ws_url=args.ws_url,
            starting_url=args.starting_url,
            goal=args.goal,
            search_algorithm=args.algorithm,
            max_depth=args.max_depth
            ,
            iterations=args.iterations
        )
    finally:
        # Clean up if logging to file
        if log_file:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log_file.close()
            logger.info(f"Closed log file: {args.log_file}")

if __name__ == "__main__":
    asyncio.run(main())