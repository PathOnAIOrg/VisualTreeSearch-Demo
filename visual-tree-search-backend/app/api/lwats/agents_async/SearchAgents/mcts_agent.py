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
        
        pass