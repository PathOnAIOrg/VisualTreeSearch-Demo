from typing import Any, Optional, Tuple, List
from datetime import datetime
import logging
import json
import time

from .tree_vis import RED, GREEN, RESET, better_print, print_trajectory, collect_all_nodes, print_entire_tree
from .lats_node import LATSNode
from .base_agent import BaseAgent
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...replay_async import generate_feedback, playwright_step_execution
from ...webagent_utils_async.browser_env.observation import extract_page_info
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation_async.evaluators import goal_finished_evaluator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MCTSAgent(BaseAgent):
    """
    Monte Carlo Tree Search Agent for web navigation tasks.
    This implementation uses reflection-based search to improve performance.
    """
    
    async def run(self, websocket=None) -> List[dict[str, Any]]:
        """
        Run the MCTS algorithm based on configuration.
        
        Args:
            websocket: Optional WebSocket connection to send updates to
            
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "Starting MCTS search",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Reset browser to initial state
        live_browser_url, session_id = await self._reset_browser(websocket)
        
        best_node = await self.mcts_search(websocket)
        print_trajectory(best_node)
        
        return best_node
    
    async def node_selection(self, node: LATSNode, websocket=None) -> Optional[LATSNode]:
        """
        Select the most promising node to expand using GPT-4.
        
        Args:
            node: Starting node for selection process
            websocket: Optional WebSocket for updates
            
        Returns:
            Selected node or None if all paths are terminal
        """
        if node.is_terminal:
            return None
            
        current_node = node
        path = [current_node]
        selection_depth = 0
        
        while current_node.children and not current_node.is_terminal:
            logger.info(f"\nSelection Step {selection_depth + 1}:")
            logger.info(f"Current node action: {current_node.action}")
            logger.info(f"Number of children: {len(current_node.children)}")
            
            # Get trajectory for GPT-4 to evaluate
            trajectory = []
            for n in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": n.natural_language_description,
                    "action": n.action,
                    "feedback": n.feedback if hasattr(n, 'feedback') else None
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
                response = self.openai_client.chat.completions.create(
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
                    logger.info(f"Selected child {selected_index + 1}: {current_node.action}")
                    logger.info(f"Selection explanation: {selection['explanation']}")
                    
                    # Send selection update if websocket is provided
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
                    logger.warning(f"Invalid child index {selected_index}, breaking selection")
                    break
                    
            except Exception as e:
                logger.error(f"Error in node selection: {str(e)}")
                if websocket:
                    await websocket.send_json({
                        "type": "selection_error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                break
            
            selection_depth += 1
            
        # Send final node selection update
        await self.websocket_node_selection(current_node, websocket=websocket)
        return current_node

    async def mcts_search(self, websocket=None) -> Optional[LATSNode]:
        """
        Perform the Monte Carlo Tree Search algorithm.
        
        Args:
            websocket: Optional WebSocket for updates
            
        Returns:
            Optional[LATSNode]: Best node found or None if search fails
        """
        best_score = float('-inf')
        best_node = None
        terminal_nodes = []
        reflection_score = 0.75  # Threshold for satisfactory solutions
        
        try:
            for i in range(self.config.iterations):
                await self.websocket_iteration_start(i, websocket=websocket)
                
                logger.info(f"\n{'='*50}")
                logger.info(f"MCTS Iteration {i + 1}/{self.config.iterations}")
                logger.info(f"{'='*50}\n")
                
                # Step 1: Node Selection
                logger.info(f"{GREEN}Step 1: Node Selection{RESET}")
                await self.websocket_step_start(step=1, step_name="node_selection", websocket=websocket)
                node = await self.node_selection(self.root_node, websocket)
                
                if node is None:
                    logger.warning("All paths lead to terminal nodes. Ending search.")
                    break
                
                # Step 2: Node Expansion
                logger.info(f"{GREEN}Step 2: Node Expansion{RESET}")
                await self.websocket_step_start(step=2, step_name="node_expansion", websocket=websocket)
                
                # Only expand if node has no children and is not terminal
                if (not node.children or len(node.children) == 0) and not node.is_terminal:
                    await self.node_expansion(node, websocket)
                    
                    # Update tree visualization if using websocket
                    tree_data = self._get_tree_data()
                    await self.websocket_tree_update("tree_update_node_expansion", tree_data, websocket)
                
                if len(node.children) == 0:
                    logger.warning(f"{RED}Node has no children, marking as terminal{RESET}")
                    node.is_terminal = True
                    continue
                
                # Step 3: Evaluate children
                logger.info(f"{GREEN}Step 3: Node Children Evaluation{RESET}")
                await self.websocket_step_start(step=3, step_name="node_children_evaluation", websocket=websocket)
                await self.node_children_evaluation(node)
                
                # Update tree visualization
                tree_data = self._get_tree_data()
                await self.websocket_tree_update("tree_update_node_children_evaluation", tree_data, websocket)
                
                # # Step 4: Select child with highest value for simulation
                # logger.info(f"{GREEN}Step 4: Simulation{RESET}")
                # await self.websocket_step_start(step=4, step_name="simulation", websocket=websocket)
                
                # # Select child with highest value for simulation
                # selected_node = max(node.children, key=lambda child: child.value)
                # await self.websocket_node_selection(selected_node, websocket=websocket, type="node_selected_for_simulation")
                
                # # Run simulation
                # reward, terminal_node = await self.simulation(selected_node, websocket=websocket)
                # terminal_nodes.append(terminal_node)
                # await self.websocket_simulation_result(reward, terminal_node, websocket=websocket)

                # Step 4: simulation using openai, no real simulation
                # TODO: implement simulation using openai
                reward, terminal_node = 0, node
                selected_node = node
                
                # Update best node if this path is better
                if reward > best_score:
                    best_score = reward
                    best_node = terminal_node
                    logger.info(f"{GREEN}New best node found! Score: {best_score:.3f}{RESET}")
                
                # If we've found a satisfactory solution, return it
                if reward >= reflection_score:
                    logger.info(f"{GREEN}Found satisfactory solution with score {reward:.3f}{RESET}")
                    await self.websocket_search_complete("success", reward, terminal_node.get_trajectory(), websocket=websocket)
                    return terminal_node
                
                # # Step 5: Backpropagation with reflection
                # logger.info(f"{GREEN}Step 5: Backpropagation{RESET}")
                # await self.websocket_step_start(step=5, step_name="backpropagation", websocket=websocket)
                
                # # Standard backpropagation
                # self.backpropagate(terminal_node, reward)

                ## Step 5: Reflection: backtracking to find the correct node
                # TODO: implement reflection-based backtracking
                # Reflection-based backtracking if score is below threshold
                if reward < reflection_score and selected_node.parent:
                    logger.info(f"Applying reflection-based backtracking (Score {reward:.3f} < {reflection_score})")
                    
                    # Create trajectory for reflection
                    path = self.get_path_to_root(terminal_node)
                    trajectory = []
                    for n in path[1:]:  # Skip root node
                        trajectory.append({
                            "natural_language_description": n.natural_language_description,
                            "action": n.action,
                            "feedback": n.feedback if hasattr(n, 'feedback') and n.feedback else "No feedback available"
                        })
                    
                    # Generate reflection prompt
                    reflection_prompt = f"""Analyze the current trajectory and suggest improvements.
                    
                    Goal: {self.goal}
                    
                    Current Trajectory:
                    {json.dumps(trajectory, indent=2)}
                    
                    Score: {reward}
                    
                    Return a JSON response with:
                    {{
                        "backtrack_to_step": int,  # Which step to backtrack to (0-based index in trajectory)
                        "reason": str,  # Why backtrack to this step
                        "suggested_improvements": [str]  # List of suggested improvements
                    }}"""
                    
                    try:
                        reflection = self.openai_client.chat.completions.create(
                            model=self.config.evaluation_model,
                            messages=[
                                {"role": "system", "content": "You are an expert at analyzing and improving search trajectories."},
                                {"role": "user", "content": reflection_prompt}
                            ],
                            response_format={"type": "json_object"}
                        )
                        
                        reflection_result = json.loads(reflection.choices[0].message.content)
                        backtrack_step = reflection_result["backtrack_to_step"]
                        
                        # Adjust backtrack step to account for root node
                        backtrack_step += 1  # +1 because trajectory skips root node
                        
                        # Prevent backtracking to root when we have actions
                        if backtrack_step == 0 and len(path) > 1:
                            backtrack_step = 1
                        
                        if 0 <= backtrack_step < len(path):
                            backtrack_node = path[backtrack_step]
                            logger.info(f"Backtracking to step {backtrack_step}")
                            logger.info(f"Reason: {reflection_result['reason']}")
                            logger.info("Suggested improvements:")
                            for improvement in reflection_result["suggested_improvements"]:
                                logger.info(f"- {improvement}")
                            
                            if websocket:
                                await websocket.send_json({
                                    "type": "backtracking",
                                    "step": backtrack_step,
                                    "node_id": id(backtrack_node),
                                    "reason": reflection_result["reason"],
                                    "suggested_improvements": reflection_result["suggested_improvements"],
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                    
                    except Exception as e:
                        logger.error(f"Error in reflection: {str(e)}")
                        if websocket:
                            await websocket.send_json({
                                "type": "reflection_error",
                                "error": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                
                # Update tree visualization after backpropagation
                tree_data = self._get_tree_data()
                await self.websocket_tree_update("tree_update_node_backpropagation", tree_data, websocket)
            
                ## Step 6: Backpropagation
                # TODO: implement backpropagation
            
            # Search completed, find best node among all nodes
            all_nodes = collect_all_nodes(self.root_node)
            all_nodes.extend(terminal_nodes)
            
            # Prefer higher reward and deeper nodes (more completed steps)
            best_node = max(all_nodes, key=lambda n: (n.reward if hasattr(n, 'reward') and n.reward is not None else 0, n.depth))
            
            if best_node.value >= 0.75:
                logger.info("Successful trajectory found")
                await self.websocket_search_complete("success", best_node.value, best_node.get_trajectory(), websocket=websocket)
            else:
                logger.info("Partially successful trajectory found")
                await self.websocket_search_complete("partial_success", best_node.value, best_node.get_trajectory(), websocket=websocket)
            
            return best_node
                
        except Exception as e:
            logger.error(f"Error in MCTS search: {str(e)}")
            
            if websocket:
                await websocket.send_json({
                    "type": "search_error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return best_node if best_node else None
    
    async def evaluate_path(self, node: LATSNode) -> float:
        """
        Evaluate a path using an LLM to score its potential for solving the goal.
        
        Args:
            node: End node of the path to evaluate
            
        Returns:
            float: Score of the path (0-1)
        """
        try:
            # Get the full path from root to this node
            path = self.get_path_to_root(node)
            
            if len(path) <= 1:  # Just the root
                return 0.0
            
            # Create trajectory for evaluation
            trajectory = []
            for n in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": n.natural_language_description,
                    "action": n.action,
                    "feedback": n.feedback if hasattr(n, 'feedback') and n.feedback else "No feedback available"
                })
            
            # Score the trajectory
            prompt = create_llm_prompt(trajectory, self.goal)
            result = score_trajectory_with_openai(prompt, self.openai_client, model=self.config.evaluation_model)
            score = result["overall_score"]
            
            logger.info(f"Path Evaluation Results:")
            logger.info(f"Overall Score: {score:.3f}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error in path evaluation: {str(e)}")
            return 0.0
