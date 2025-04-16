from typing import Any, Optional, Tuple, List
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from .tree_vis import RED, better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .lats_node import LATSNode
from .base_agent import BaseAgent

class MCTSAgent(BaseAgent):
    async def run(self, websocket=None) -> list[LATSNode]:
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "Starting MCTS search",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        best_node = await self.mcts_search(websocket)
        print_trajectory(best_node)
        return best_node
    

    # Performs Monte Carlo Tree Search starting from the root node with WebSocket updates.
    # Uses GPT-4 for node selection and reflection-based backpropagation.
    async def mcts_search(self, websocket=None):
        for i in range(self.config.iterations):
            await self.websocket_iteration_start(i, websocket=websocket)
                
            print(f"Iteration {i}/{self.config.iterations} ...")

            # Step 1: Node Selection
            # Selection: Use GPT-4 to select a promising path


            # Step 2: Node Expansion
            # Expansion: Expand the selected node if possible


            # Step 3: Node Simulation
            # Simulation: Evaluate the current path


            # Step 4: Backpropagation
            # # Reflection-based backpropagation
