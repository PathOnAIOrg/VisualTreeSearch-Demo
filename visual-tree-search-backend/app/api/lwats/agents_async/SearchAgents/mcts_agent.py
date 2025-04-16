from typing import Any, Optional, Tuple, List
from datetime import datetime
from dotenv import load_dotenv
import json

from .tree_vis import RED, better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .lats_node import LATSNode
from .base_agent import BaseAgent
import openai

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
    # TODO: if we select non-leaf node, do we expand the node again?
    # TODO: modify node selection logic to choose between the node and the children of the node, 
    async def node_selection(self, node: LATSNode, websocket=None) -> Optional[LATSNode]:
        # start from the root node
        if node.is_terminal:
            return None
            
        current_node = node
        path = [current_node]
        selection_depth = 0
        
        while current_node.children and not current_node.is_terminal:
            print(f"\nSelection Step {selection_depth + 1}:")
            print(f"Current node action: {current_node.action}")
            print(f"Number of children: {len(current_node.children)}")
            
            # Get trajectory for GPT-4 to evaluate
            trajectory = []
            for node in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": node.natural_language_description,
                    "action": node.action,
                    "feedback": node.feedback if hasattr(node, 'feedback') else None
                })
            
            # Create prompt for GPT-4
            prompt = f"""Given the current trajectory and goal, select the most promising child node to explore next.
            Consider the overall progress, efficiency, and likelihood of success.
            
            Goal: {self.goal}
            
            Current Trajectory:
            {json.dumps(trajectory, indent=2)}
            
            Available Children:
            {json.dumps([{
                'action': child.action,
                'description': child.natural_language_description,
                'visits': child.visits,
                'value': child.value if hasattr(child, 'value') else 0
            } for child in current_node.children], indent=2)}
            
            Return a JSON response with:
            {{
                "selected_child_index": int,  # Index of the selected child
                "explanation": str  # Brief explanation of the selection
            }}"""
            
            try:
                response = openai.ChatCompletion.create(
                    model=self.config.evaluation_model,
                    messages=[
                        {"role": "system", "content": "You are an expert at selecting promising paths in a search tree."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                selection = json.loads(response.choices[0].message.content)
                selected_index = selection["selected_child_index"]
                
                if 0 <= selected_index < len(current_node.children):
                    current_node = current_node.children[selected_index]
                    path.append(current_node)
                    print(f"Selected child {selected_index + 1}: {current_node.action}")
                    print(f"Selection explanation: {selection['explanation']}")
                    
                    if websocket:
                        await websocket.send_json({
                            "type": "node_selected",
                            "node_id": id(current_node),
                            "parent_id": id(current_node.parent),
                            "action": current_node.action,
                            "description": current_node.natural_language_description,
                            "explanation": selection["explanation"],
                            "depth": selection_depth + 1,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                else:
                    print(f"Invalid child index {selected_index}, breaking selection")
                    break
                    
            except Exception as e:
                print(f"Error in node selection: {str(e)}")
                if websocket:
                    await websocket.send_json({
                        "type": "selection_error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                break
            
            selection_depth += 1
            
        return current_node

    async def mcts_search(self, websocket=None):
        for i in range(self.config.iterations):
            await self.websocket_iteration_start(i, websocket=websocket)
                
            print(f"Iteration {i}/{self.config.iterations} ...")

            # Step 1: Node Selection
            # Selection: Use GPT-4 to select a promising path
            print(f"{GREEN}Step 1: node selection{RESET}")
            await self.websocket_step_start(step=1, step_name="node_selection", websocket=websocket)
            node = await self.node_selection(self.root_node)
            await self.websocket_node_selection(node, websocket=websocket)

            if node is None:
                print("All paths lead to terminal nodes with reward 0. Ending search.")
                break



            # Step 2: Node Expansion
            # Expansion: Expand the selected node if possible


            # Step 3: Node Simulation
            # Simulation: Evaluate the current path


            # Step 4: Backpropagation
            # # Reflection-based backpropagation
