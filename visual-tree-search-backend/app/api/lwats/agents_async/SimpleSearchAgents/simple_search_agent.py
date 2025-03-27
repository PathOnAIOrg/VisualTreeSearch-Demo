import logging
import time
from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime
import os
import json
import subprocess

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import aiohttp

from ...core_async.config import AgentConfig

from ...webagent_utils_async.action.highlevel import HighLevelActionSet
from ...webagent_utils_async.utils.playwright_manager import AsyncPlaywrightManager, setup_playwright
from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation_async.evaluators import goal_finished_evaluator
from ...replay_async import generate_feedback, playwright_step_execution
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.browser_env.observation import extract_page_info
from .lats_node import LATSNode
from .tree_vis import better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...webagent_utils_async.utils.utils import urls_to_images

logger = logging.getLogger(__name__)
openai_client = OpenAI()

class SimpleSearchAgent:
    def __init__(
        self,
        starting_url: str,
        messages: list[dict[str, Any]],
        goal: str,
        images: list,
        playwright_manager: AsyncPlaywrightManager,
        config: AgentConfig,
    ):
        self.starting_url = starting_url
        self.goal = goal
        self.image_urls = images
        self.images = urls_to_images(self.image_urls)
        self.messages = messages
        self.messages.append({"role": "user", "content": f"The goal is: {self.goal}"})

        self.playwright_manager = playwright_manager

        self.config = config

        self.agent_type = ["bid", "nav", "file", "select_option"]
        self.action_set = HighLevelActionSet(
            subsets=self.agent_type, strict=False, multiaction=True, demo_mode="default"
        )
        self.root_node = LATSNode(
            natural_language_description=None,
            action=None,
            prob=None,
            element=None,
            goal=self.goal,
            parent=None
        )
        self.reset_url = os.environ["ACCOUNT_RESET_URL"]


    async def run(self, websocket=None) -> List[Dict[str, Any]]:
        """
        Run the search algorithm based on configuration.
        
        Args:
            websocket: Optional WebSocket connection to send updates to
            
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
            
        Raises:
            ValueError: If the search algorithm is not supported
        """
        algorithm = self.config.search_algorithm.lower()
        
        if algorithm == "bfs":
            logger.info("Starting BFS algorithm")
            if websocket:
                return await self.bfs_with_websocket(websocket)
            else:
                return await self.bfs()
        elif algorithm == "dfs":
            logger.info("Starting DFS algorithm")
            if websocket:
                return await self.dfs_with_websocket(websocket)
            else:
                return await self.dfs()
        else:
            error_msg = f"Unsupported algorithm: {algorithm}"
            logger.error(error_msg)
            if websocket:
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
            raise ValueError(error_msg)

    async def _reset_browser(self, websocket=None) -> Optional[str]:
        """Reset the browser to initial state and return the live browser URL if available."""
        await self.playwright_manager.close()
        
        ## reset account using api-based account reset
        if self.config.account_reset:
            if websocket:
                await websocket.send_json({
                    "type": "account_reset",
                    "status": "started",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            try:
                # Use aiohttp instead of curl
                async with aiohttp.ClientSession() as session:
                    headers = {'Connection': 'close'}  # Similar to curl -N
                    async with session.get(self.reset_url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"Account reset successful: {data}")
                            if websocket:
                                await websocket.send_json({
                                    "type": "account_reset",
                                    "status": "success",
                                    "data": data,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                        else:
                            error_msg = f"Account reset failed with status {response.status}"
                            print(error_msg)
                            if websocket:
                                await websocket.send_json({
                                    "type": "account_reset",
                                    "status": "failed",
                                    "reason": error_msg,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            
            except Exception as e:
                print(f"Error during account reset: {e}")
                if websocket:
                    await websocket.send_json({
                        "type": "account_reset",
                        "status": "failed",
                        "reason": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })

        try:
            # Create new playwright manager
            self.playwright_manager = await setup_playwright(
                storage_state=self.config.storage_state,
                headless=self.config.headless,
                mode=self.config.browser_mode
            )
            page = await self.playwright_manager.get_page()
            live_browser_url = None
            if self.config.browser_mode == "browserbase":
                live_browser_url = await self.playwright_manager.get_live_browser_url()
            await page.goto(self.starting_url, wait_until="networkidle")
            
            # Send success message if websocket is provided
            if websocket:
                if self.config.storage_state:
                    await websocket.send_json({
                        "type": "browser_setup",
                        "status": "success",
                        "message": f"Browser successfully initialized with storage state file: {self.config.storage_state}",
                        "live_browser_url": live_browser_url,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    await websocket.send_json({
                        "type": "browser_setup",
                        "status": "success",
                        "message": "Browser successfully initialized",
                        "live_browser_url": live_browser_url,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return live_browser_url
        except Exception as e:
            print(f"Error setting up browser: {e}")
            if websocket:
                await websocket.send_json({
                    "type": "browser_setup",
                    "status": "failed",
                    "reason": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            return None

    async def expand(self, node: LATSNode, websocket=None) -> None:
        """
        Expand a node by generating its children.
        
        Args:
            node: Node to expand
            websocket: Optional WebSocket connection to send updates to
        """
        children_state = await self.generate_children(node, websocket)
        for child_state in children_state:
            child = LATSNode(
                natural_language_description=child_state["natural_language_description"],
                action=child_state["action"],
                prob=child_state["prob"],
                element=child_state["element"],
                goal=node.goal,
                parent=node
            )
            node.children.append(child)
            
            # Send child creation update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "node_created",
                    "node_id": id(child),
                    "parent_id": id(node),
                    "action": child.action,
                    "description": child.natural_language_description,
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def generate_children(self, node: LATSNode, websocket=None) -> list[dict]:
        """
        Generate child nodes for a given node.
        
        Args:
            node: Parent node to generate children for
            websocket: Optional WebSocket connection to send updates to
            
        Returns:
            list[dict]: List of child state dictionaries
        """
        # Reset browser and get live URL
        live_browser_url = await self._reset_browser(websocket)
        
        # Send browser URL update if websocket is provided
        if websocket and live_browser_url:
            await websocket.send_json({
                "type": "browser_url_update",
                "live_browser_url": live_browser_url,
                "node_id": id(node),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        path = self.get_path_to_root(node)
        
        # Execute path
        for n in path[1:]:  # Skip root node
            if websocket:
                await websocket.send_json({
                    "type": "replaying_action",
                    "node_id": id(n),
                    "action": n.action,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            success = await playwright_step_execution(
                n,
                self.goal,
                self.playwright_manager,
                is_replay=False,
                log_folder=self.config.log_folder
            )
            if not success:
                n.is_terminal = True
                if websocket:
                    await websocket.send_json({
                        "type": "replay_failed",
                        "node_id": id(n),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                return []
            
            if not n.feedback:
                n.feedback = await generate_feedback(
                    self.goal,
                    n.natural_language_description,
                    self.playwright_manager,
                )
                if websocket:
                    await websocket.send_json({
                        "type": "feedback_generated",
                        "node_id": id(n),
                        "feedback": n.feedback,
                        "timestamp": datetime.utcnow().isoformat()
                    })

        time.sleep(3)
        page = await self.playwright_manager.get_page()
        page_info = await extract_page_info(page, self.config.fullpage, self.config.log_folder)

        messages = [{"role": "user", "content": f"Action is: {n.action}"} for n in path[1:]]
        
        if websocket:
            await websocket.send_json({
                "type": "generating_actions",
                "node_id": id(node),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        next_actions = await extract_top_actions(
            [{"natural_language_description": n.natural_language_description, "action": n.action, "feedback": n.feedback} for n in path[1:]],
            self.goal,
            self.images, 
            page_info,
            self.action_set,
            openai_client,
            features=self.config.features,
            elements_filter=self.config.elements_filter,
            branching_factor=self.config.branching_factor,
            log_folder=self.config.log_folder,
            fullpage=self.config.fullpage,
            action_generation_model=self.config.action_generation_model,
            action_grounding_model=self.config.action_grounding_model
        )

        children = []
        for action in next_actions:
            if action["action"] == "FINISH":
                if action["prob"] > 0.2:
                    node.is_terminal = True
                    if websocket:
                        await websocket.send_json({
                            "type": "node_terminal",
                            "node_id": id(node),
                            "reason": "finish_action",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    return []
                continue
            
            page = await self.playwright_manager.get_page()
            code, function_calls = self.action_set.to_python_code(action["action"])

            if len(function_calls) == 1:
                try:
                    for function_name, function_args in function_calls:
                        extracted_number = parse_function_args(function_args)
                        element = await locate_element(page, extracted_number)
                        action["element"] = element
                except Exception as e:
                    action["element"] = None
                    if websocket:
                        await websocket.send_json({
                            "type": "element_location_failed",
                            "action": action["action"],
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                children.append(action)

        if not children:
            node.is_terminal = True
            if websocket:
                await websocket.send_json({
                    "type": "node_terminal",
                    "node_id": id(node),
                    "reason": "no_valid_actions",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return children
    
    def get_path_to_root(self, node: LATSNode) -> List[LATSNode]:
        path = []
        current = node
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    async def bfs(self) -> List[Dict[str, Any]]:
        """
        Performs breadth-first search starting from the root node.
        Skips nodes that are marked as terminal.
        
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        queue = deque([self.root_node])
        best_score = float('-inf')
        best_path = None
        
        while queue:
            current_node = queue.popleft()
            print("print the trajectory")
            print_trajectory(current_node)
            print("print the entire tree")
            print_entire_tree(self.root_node)
            
            # Skip terminal nodes
            if current_node.is_terminal:
                continue
                
            # Expand current node if it hasn't been expanded yet
            if not current_node.children:
                await self.expand(current_node)
                
            # Get the path from root to this node
            path = self.get_path_to_root(current_node)
            
            # Create trajectory for scoring
            trajectory = []
            for node in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": node.natural_language_description,
                    "action": node.action,
                    "feedback": node.feedback
                })
            
            # Score the trajectory
            prompt = create_llm_prompt(trajectory, self.goal)
            result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)

            score = result["overall_score"]
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = path
                    
            logger.info(f"Node score: {score}")
            
            # If we've found a satisfactory solution, return it
            if score >= 0.75:
                logger.info("Found satisfactory solution")
                return [{"action": node.action} for node in path[1:]]
            
            # Add non-terminal children to queue
            for child in current_node.children:
                if not child.is_terminal and child not in queue:
                    queue.append(child)
        
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            logger.info(f"Returning best path found with score {best_score}")
            return [{"action": node.action} for node in best_path[1:]]
        
        # If no path was found at all
        logger.warning("No valid path found")
        return []

    async def dfs(self) -> List[Dict[str, Any]]:
        """
        Performs depth-first search starting from the root node.
        Skips nodes that are marked as terminal.
        
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        stack = [self.root_node]
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        
        def evaluate_node(node: LATSNode) -> tuple[float, bool]:
            """
            Evaluate a node's trajectory.
            
            Returns:
                tuple[float, bool]: (score, should_terminate)
            """
            path = self.get_path_to_root(node)
            trajectory = []
            for n in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": n.natural_language_description,
                    "action": n.action,
                    "feedback": n.feedback
                })
            
            prompt = create_llm_prompt(trajectory, self.goal)
            result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)

            score = result["overall_score"]
            
            logger.info(f"Node score: {score}")
            
            return score, score >= 0.75
        
        while stack:
            current_node = stack.pop()
            print("print the trajectory")
            print_trajectory(current_node)
            print("print the entire tree")
            print_entire_tree(self.root_node)
            
            # Skip if we've already visited this node or if it's terminal
            if current_node in visited or current_node.is_terminal:
                continue
                
            visited.add(current_node)
            
            # Expand current node if it hasn't been expanded yet
            if not current_node.children:
                await self.expand(current_node)
                
            score, should_terminate = evaluate_node(current_node)
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = self.get_path_to_root(current_node)
                
            # If we've found a satisfactory solution, return it
            if should_terminate:
                logger.info("Found satisfactory solution")
                return [{"action": node.action} for node in best_path[1:]]
            
            # Add non-terminal children to stack in reverse order
            for child in reversed(current_node.children):
                if not child.is_terminal and child not in visited:
                    stack.append(child)
                    
            # Optional: Add depth-based cutoff
            if current_node.depth >= self.config.max_depth:
                logger.info(f"Reached maximum depth {self.config.max_depth}")
                continue
        
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            logger.info(f"Returning best path found with score {best_score}")
            return [{"action": node.action} for node in best_path[1:]]
        
        # If no path was found at all
        logger.warning("No valid path found")
        return []

    async def bfs_with_websocket(self, websocket=None) -> List[Dict[str, Any]]:
        """
        Performs breadth-first search starting from the root node with WebSocket updates.
        Skips nodes that are marked as terminal.
        
        Args:
            websocket: Optional WebSocket connection to send updates to
            
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        queue = deque([self.root_node])
        best_score = float('-inf')
        best_path = None
        
        # Get the live browser URL during initial setup
        live_browser_url = await self._reset_browser(websocket)
        
        # Send initial status if websocket is provided
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "BFS search started",
                "timestamp": datetime.utcnow().isoformat(),
                "live_browser_url": live_browser_url  # Include the live browser URL
            })
        
        while queue:
            current_node = queue.popleft()
            
            # Check if we've reached the maximum depth
            if current_node.depth >= self.config.max_depth:
                if websocket:
                    await websocket.send_json({
                        "type": "node_terminal",
                        "node_id": id(current_node),
                        "reason": "depth_limit",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                continue
            
            # Send node processing update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "node_processing",
                    "node_id": id(current_node),
                    "depth": current_node.depth,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Print debug info
            print("print the trajectory")
            print_trajectory(current_node)
            print("print the entire tree")
            print_entire_tree(self.root_node)
            
            # Skip terminal nodes
            if current_node.is_terminal:
                if websocket:
                    await websocket.send_json({
                        "type": "node_terminal",
                        "node_id": id(current_node),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                continue
                
            # Expand current node if it hasn't been expanded yet
            if not current_node.children:
                if websocket:
                    await websocket.send_json({
                        "type": "node_expanding",
                        "node_id": id(current_node),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Pass the websocket to expand method
                await self.expand(current_node, websocket)
                
                # Send tree update after expansion
                if websocket:
                    tree_data = self._get_tree_data()
                    await websocket.send_json({
                        "type": "tree_update",
                        "tree": tree_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Get the path from root to this node
            path = self.get_path_to_root(current_node)
            
            # Create trajectory for scoring
            trajectory = []
            for node in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": node.natural_language_description,
                    "action": node.action,
                    "feedback": node.feedback
                })
            
            # Score the trajectory
            prompt = create_llm_prompt(trajectory, self.goal)
            result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)

            score = result["overall_score"]
            
            # Send score update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "node_scored",
                    "node_id": id(current_node),
                    "score": score,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = path
                
                # Send best path update if websocket is provided
                if websocket:
                    await websocket.send_json({
                        "type": "best_path_update",
                        "score": best_score,
                        "path": [{"id": id(node), "action": node.action} for node in best_path[1:]],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            logger.info(f"Node score: {score}")
            
            # If we've found a satisfactory solution, return it
            if score >= 0.75:
                logger.info("Found satisfactory solution")
                
                # Send completion update if websocket is provided
                if websocket:
                    await websocket.send_json({
                        "type": "search_complete",
                        "status": "success",
                        "score": score,
                        "path": [{"id": id(node), "action": node.action} for node in path[1:]],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                return [{"action": node.action} for node in path[1:]]
            
            # Add non-terminal children to queue
            for child in current_node.children:
                if not child.is_terminal and child not in queue:
                    queue.append(child)
                    
                    # Send queue update if websocket is provided
                    if websocket:
                        await websocket.send_json({
                            "type": "node_queued",
                            "node_id": id(child),
                            "parent_id": id(current_node),
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            logger.info(f"Returning best path found with score {best_score}")
            
            # Send completion update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "search_complete",
                    "status": "partial_success",
                    "score": best_score,
                    "path": [{"id": id(node), "action": node.action} for node in best_path[1:]],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return [{"action": node.action} for node in best_path[1:]]
        
        # If no path was found at all
        logger.warning("No valid path found")
        
        # Send failure update if websocket is provided
        if websocket:
            await websocket.send_json({
                "type": "search_complete",
                "status": "failure",
                "message": "No valid path found",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return []

    async def dfs_with_websocket(self, websocket=None) -> List[Dict[str, Any]]:
        """
        Performs depth-first search starting from the root node with WebSocket updates.
        Skips nodes that are marked as terminal.
        
        Args:
            websocket: Optional WebSocket connection to send updates to
            
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        stack = [self.root_node]
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        
        # Get the live browser URL during initial setup
        live_browser_url = await self._reset_browser(websocket)
        
        # Send initial status if websocket is provided
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "DFS search started",
                "timestamp": datetime.utcnow().isoformat(),
                "live_browser_url": live_browser_url
            })
        
        while stack:
            current_node = stack.pop()
            
            # Skip if we've already visited this node
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            # Check if we've reached the maximum depth
            if current_node.depth >= self.config.max_depth:
                if websocket:
                    await websocket.send_json({
                        "type": "node_terminal",
                        "node_id": id(current_node),
                        "reason": "depth_limit",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                continue
            
            # Send node processing update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "node_processing",
                    "node_id": id(current_node),
                    "depth": current_node.depth,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Print debug info
            print("print the trajectory")
            print_trajectory(current_node)
            print("print the entire tree")
            print_entire_tree(self.root_node)
            
            # Skip terminal nodes
            if current_node.is_terminal:
                if websocket:
                    await websocket.send_json({
                        "type": "node_terminal",
                        "node_id": id(current_node),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                continue
                
            # Expand current node if it hasn't been expanded yet
            if not current_node.children:
                if websocket:
                    await websocket.send_json({
                        "type": "node_expanding",
                        "node_id": id(current_node),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Pass the websocket to expand method
                await self.expand(current_node, websocket)
                
                # Send tree update after expansion
                if websocket:
                    tree_data = self._get_tree_data()
                    await websocket.send_json({
                        "type": "tree_update",
                        "tree": tree_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Get the path from root to this node
            path = self.get_path_to_root(current_node)
            
            # Create trajectory for scoring
            trajectory = []
            for node in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": node.natural_language_description,
                    "action": node.action,
                    "feedback": node.feedback
                })
            
            # Score the trajectory
            prompt = create_llm_prompt(trajectory, self.goal)
            result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)

            score = result["overall_score"]
            
            # Send score update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "node_scored",
                    "node_id": id(current_node),
                    "score": score,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = path
                
                # Send best path update if websocket is provided
                if websocket:
                    await websocket.send_json({
                        "type": "best_path_update",
                        "score": best_score,
                        "path": [{"id": id(node), "action": node.action} for node in best_path[1:]],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            logger.info(f"Node score: {score}")
            
            # If we've found a satisfactory solution, return it
            if score >= 0.75:
                logger.info("Found satisfactory solution")
                
                # Send completion update if websocket is provided
                if websocket:
                    await websocket.send_json({
                        "type": "search_complete",
                        "status": "success",
                        "score": score,
                        "path": [{"id": id(node), "action": node.action} for node in path[1:]],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                return [{"action": node.action} for node in path[1:]]
            
            # Add non-terminal children to stack in reverse order
            for child in reversed(current_node.children):
                if not child.is_terminal and child not in visited:
                    stack.append(child)
                    
                    # Send stack update if websocket is provided
                    if websocket:
                        await websocket.send_json({
                            "type": "node_stacked",
                            "node_id": id(child),
                            "parent_id": id(current_node),
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            logger.info(f"Returning best path found with score {best_score}")
            
            # Send completion update if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "search_complete",
                    "status": "partial_success",
                    "score": best_score,
                    "path": [{"id": id(node), "action": node.action} for node in best_path[1:]],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return [{"action": node.action} for node in best_path[1:]]
        
        # If no path was found at all
        logger.warning("No valid path found")
        
        # Send failure update if websocket is provided
        if websocket:
            await websocket.send_json({
                "type": "search_complete",
                "status": "failure",
                "message": "No valid path found",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return []

    def _get_tree_data(self):
        """Get tree data in a format suitable for visualization"""
        nodes = collect_all_nodes(self.root_node)
        tree_data = []
        
        for node in nodes:
            node_data = {
                "id": id(node),
                "parent_id": id(node.parent) if node.parent else None,
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description,
                "depth": node.depth,
                "is_terminal": node.is_terminal
            }
            tree_data.append(node_data)
        
        return tree_data

