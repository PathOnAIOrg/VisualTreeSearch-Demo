from typing import Any, Optional, Tuple, List
from datetime import datetime
import logging
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from .tree_vis import RED, GREEN, RESET, better_print, print_trajectory, collect_all_nodes, print_entire_tree
from .lats_node import LATSNode
from .base_agent import BaseAgent
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...replay_async import generate_feedback, playwright_step_execution
from ...webagent_utils_async.browser_env.observation import extract_page_info
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation_async.evaluators import goal_finished_evaluator

openai_client = OpenAI()

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
        # if websocket:
        #     await websocket.send_json({
        #         "type": "search_status",
        #         "status": "started",
        #         "message": "Starting MCTS search",
        #         "timestamp": datetime.utcnow().isoformat()
        #     })
        
        # Reset browser to initial state
        live_browser_url, session_id = await self._reset_browser(websocket)
        
        best_node = await self.mcts_search(websocket)
        print_trajectory(best_node)
        
        return best_node
    
    async def node_selection(self, node: LATSNode, websocket=None) -> Optional[LATSNode]:
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
            
            response = openai_client.chat.completions.create(
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
            else:
                logger.warning(f"Invalid child index {selected_index}, breaking selection")
                break
                    
            
            selection_depth += 1
            
        # Send final node selection update
        await self.websocket_node_selection(current_node, websocket=websocket)
        return current_node

    async def evaluate_selected_path(self, path) -> None:
        """Evaluate the current node and assign its score."""
        # Get the path from root to this node
        # path = self.get_path_to_root(node)
        
        # Create trajectory for scoring (skip root node)
        trajectory = []
        for n in path[1:]:  # Skip root node
            trajectory.append({
                "natural_language_description": n.natural_language_description,
                "action": n.action,
                "feedback": n.feedback
            })
        
        ## fix for MCTS agent only
        if len(trajectory) == 0:
            score = 0
            return score
        prompt = create_llm_prompt(trajectory, self.goal)
        print(f"prompt: {prompt}")
        result = score_trajectory_with_openai(
            prompt, 
            openai_client, 
            model=self.config.evaluation_model
        )
        print(f"result: {result}")
        score = result["overall_score"]
        print(f"Simulation Results, evaluate selected path:")
        print(f"Overall Score: {score:.3f}")
        print(f"Efficiency Score: {result['efficiency_score']:.3f}")
        print(f"Accuracy Score: {result['accuracy_score']:.3f}")
        print(f"Robustness Score: {result['robustness_score']:.3f}")
        return score
    
    async def websocket_reflection_backtracking(self, path, selected_node, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "reflection_backtracking",
                "path": [node.action for node in path if node.action is not None],
                "node_id": id(selected_node),
                "node_parent_id": id(selected_node.parent),
                "node_action": selected_node.action,
                "node_description": selected_node.natural_language_description,
                "trajectory": selected_node.get_trajectory()
            })

    async def reflection_backtracking(self, path) -> List[LATSNode]:
        """
        Implement reflection-based backtracking to improve search trajectory.
        
        Args:
            node: Current node
            path: Current path from root to node
            
        Returns:
            List[LATSNode]: Modified path after backtracking
        """
        # Create trajectory for reflection
        trajectory = []
        for n in path[1:]:  # Skip root node
            trajectory.append({
                "natural_language_description": n.natural_language_description,
                "action": n.action,
                "feedback": n.feedback if hasattr(n, 'feedback') else None
            })
        
        score = await self.evaluate_selected_path(path)
        print(f"\nReflection Step (Score {score:.3f} < {self.config.reflection_score}):")
        
        # Generate reflection prompt
        reflection_prompt = f"""Analyze the current trajectory and suggest improvements for the current website.
        
        Goal: {self.goal}
        
        Current Trajectory:
        {json.dumps(trajectory, indent=2)}
        
        Score: {score}
        
        Return a JSON response with:
        {{
            "backtrack_to_step": int,  # Which step to backtrack to (0-based index)
            "reason": str,  # Why backtrack to this step
            "suggested_improvements": [str]  # List of suggested improvements specific to current websites
        }}"""
        
        reflection = openai_client.chat.completions.create(
            model=self.config.evaluation_model,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing and improving search trajectories."},
                {"role": "user", "content": reflection_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        reflection_result = json.loads(reflection.choices[0].message.content)
        backtrack_step = reflection_result["backtrack_to_step"]
        
        # Backtrack to the suggested step
        if 0 <= backtrack_step < len(path):
            # Prevent backtracking to root when we have actions
            if backtrack_step == 0 and len(path) > 1:
                backtrack_step = 1
                print("Adjusted backtracking to maintain at least one action")
            
            current_node = path[backtrack_step]
            # Remove nodes after the backtrack point
            while len(path) > backtrack_step + 1:
                path.pop()
                
            print(f"Backtracking to step {backtrack_step}")
            print(f"Reason: {reflection_result['reason']}")
            print("Suggested improvements:")
            for improvement in reflection_result["suggested_improvements"]:
                print(f"- {improvement}")
            print(f"current_node: {current_node.action}")
            print(f"current_node: {current_node.natural_language_description}")
        
        return path, current_node

    async def mcts_search(self, websocket=None) -> Optional[LATSNode]:
        best_score = float('-inf')
        best_node = None
        print(f"iterations: {self.config.iterations}")
        
        for i in range(self.config.iterations):
            await self.websocket_iteration_start(i, websocket=websocket)
            
            print(f"\n{'='*50}")
            print(f"MCTS Iteration {i + 1}/{self.config.iterations}")
            print(f"{'='*50}\n")
            
            # Step 1: Node Selection (contain simulation)
            # "node selection" combines selection and partial simulation
            print(f"{GREEN}Step 1: Node Selection{RESET}")
            await self.websocket_step_start(step=1, step_name="node_selection", websocket=websocket)
            selected_node = await self.node_selection(self.root_node, websocket)
            # await self.websocket_node_selection(selected_node, websocket=websocket)
            # tree_data = self._get_tree_data()
            # if websocket:
            #     await self.websocket_tree_update(type="tree_update_node_selection", websocket=websocket, tree_data=tree_data)
            # else:
            #     print_entire_tree(self.root_node)
            
            if selected_node is None:
                logger.warning("All paths lead to terminal nodes. Ending search.")
                break
            
            # Step 2: Node Expansion
            print(f"{GREEN}Step 2: Node Expansion{RESET}")
            await self.websocket_step_start(step=2, step_name="node_expansion", websocket=websocket)
            if selected_node.depth < self.config.max_depth :
                await self.node_expansion(selected_node, websocket)
                if selected_node is None:
                    # all the nodes are terminal, stop the search
                    print(f"{RED}All nodes are terminal, stopping search{RESET}")
                    break
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_expansion", websocket=websocket, tree_data=tree_data)
                else:
                    print_entire_tree(self.root_node)
            

            # optional: prior value
            if self.config.set_prior_value:
                await self.websocket_step_start(step=2, step_name="node_children_evaluation", websocket=websocket)
                await self.node_children_evaluation(selected_node)
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_children_evaluation", websocket=websocket, tree_data=tree_data)
                else:
                    print("after evaluation")
                    print_entire_tree(self.root_node)

            # Step 3: simulation using the current node, (generate a path using the current node, and score the path)
            # TODO: implement simulation using openai
            print(f"{GREEN}Step 3: Simulation{RESET}")
            await self.websocket_step_start(step=3, step_name="simulation", websocket=websocket)
            path = self.get_path_to_root(selected_node)
            # here score is the reward
            score = await self.evaluate_selected_path(path)
            # change to reward later?
            if score > best_score:
                best_score = score
                best_path = path
                best_node = selected_node
                print(f"\nNew best path found!")
                print(f"best score: {best_score:.3f}")
                print(f"best node: {best_node.action}")
                print(f"best node: {best_node.natural_language_description}")
                print(f"best path: {best_path}")

            # add websocket information, just use websocket here
            if websocket:
                await self.websocket_simulation_result(score, selected_node, websocket=websocket)


            ## Step 4: reflection backtracking
            print(f"{GREEN}Step 4: Reflection Backtracking{RESET}")
            await self.websocket_step_start(step=4, step_name="reflection_backtracking", websocket=websocket)
            if score >= self.config.reflection_score:
                # Convert path to serializable trajectory
                # trajectory = [node.action for node in path if node.action is not None]
                await self.websocket_search_complete("success", score, selected_node.get_trajectory(), websocket=websocket)
                await self.playwright_manager.close()
                return selected_node

            print(f"path: {path}")
            path, current_node = await self.reflection_backtracking(path)
            print(f"path: {path}")
            print(f"current_node: {current_node.action}")
            print(f"current_node: {current_node.natural_language_description}")

            # add websocket information, just use websocket here
            if websocket:
                await self.websocket_reflection_backtracking(path, current_node, websocket=websocket)

            # Step 5: backpropagation
            print(f"{GREEN}Step 5: Backpropagation{RESET}")
            await self.websocket_step_start(step=5, step_name="backpropagation", websocket=websocket)
            for node in path:
                if node != self.root_node:
                    old_value = node.value
                    node.visits += 1
                    node.value += (score - node.value) / node.visits
                    # consiste with lats backpropagation
                    #node.value = (node.value * (node.visits - 1) + score) / node.visits
                    print(f"Node {node.action}:")
                    print(f"  Visits: {node.visits}")
                    print(f"  Value: {old_value:.3f} -> {node.value:.3f}")
                # add websocket information, just use websocket here
                # if websocket:
                #     await websocket.send_json({
                #         "type": "backpropagation",
                #         "node_id": id(node),
                #         "node_parent_id": id(node.parent),
                #         "node_action": node.action,
                #         "node_value": node.value,
                #         "node_visits": node.visits,
                #         "node_old_value": old_value,
                #         "node_description": node.natural_language_description,
                #     })

            tree_data = self._get_tree_data()
            print_entire_tree(self.root_node)
            print(tree_data)
            if websocket:
                await self.websocket_tree_update(type="tree_update_node_backpropagation", websocket=websocket, tree_data=tree_data)
            else:
                print_entire_tree(self.root_node)
        if best_node:
             # Convert node to serializable trajectory
            # trajectory = [n.action for n in self.get_path_to_root(best_node) if n.action is not None]
            await self.websocket_search_complete("partial_success", best_node.value, best_node.get_trajectory(), websocket=websocket)
        await self.playwright_manager.close()
        return best_node
