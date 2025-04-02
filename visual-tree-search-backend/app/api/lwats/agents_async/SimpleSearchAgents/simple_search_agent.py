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
        elif algorithm == "rmcts":
            logger.info("Starting Reflective MCTS algorithm")
            return await self.rmcts()
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
                session_id = await self.playwright_manager.get_session_id()
            else:
                session_id = None
                live_browser_url = None
            await page.goto(self.starting_url, wait_until="networkidle")
            
            # Send success message if websocket is provided
            if websocket:
                if self.config.storage_state:
                    await websocket.send_json({
                        "type": "browser_setup",
                        "status": "success",
                        "message": f"Browser successfully initialized with storage state file: {self.config.storage_state}",
                        "live_browser_url": live_browser_url,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    await websocket.send_json({
                        "type": "browser_setup",
                        "status": "success",
                        "message": "Browser successfully initialized",
                        "live_browser_url": live_browser_url,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return live_browser_url, session_id
        except Exception as e:
            print(f"Error setting up browser: {e}")
            if websocket:
                await websocket.send_json({
                    "type": "browser_setup",
                    "status": "failed",
                    "reason": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            return None, None

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
        live_browser_url, session_id = await self._reset_browser(websocket)
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
        queue_set = {self.root_node}  # Track nodes in queue
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        current_level = 0  # Track current level for BFS
        
        try:
            while queue:
                # Process all nodes at current level
                level_size = len(queue)
                current_level += 1
                level_nodes = []  # Store nodes at current level for later processing
                
                # First, expand all nodes at current level
                for _ in range(level_size):
                    current_node = queue.popleft()
                    queue_set.remove(current_node)  # Remove from queue tracking
                    
                    # Skip if we've already visited this node
                    if current_node in visited:
                        continue
                        
                    visited.add(current_node)
                    
                    # Skip terminal nodes
                    if current_node.is_terminal:
                        logger.info(f"Node {id(current_node)} is terminal")
                        continue
                    
                    # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
                    if not current_node.children and current_node.depth < self.config.max_depth:
                        try:
                            await self.expand(current_node)
                        except Exception as e:
                            error_msg = f"Error expanding node {id(current_node)}: {str(e)}"
                            logger.error(error_msg)
                            current_node.is_terminal = True
                            continue
                    
                    # Store node for later processing
                    level_nodes.append(current_node)
                    
                    # Add non-terminal children to queue for next level if they haven't reached max_depth
                    for child in current_node.children:
                        if not child.is_terminal and child not in visited and child not in queue_set and child.depth < self.config.max_depth:
                            queue.append(child)
                            queue_set.add(child)  # Add to queue tracking
                
                # Now process all nodes at current level
                for current_node in level_nodes:
                    print("print the trajectory")
                    print_trajectory(current_node)
                    print("print the entire tree")
                    print_entire_tree(self.root_node)
                    
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
                    
                    try:
                        # Score the trajectory
                        prompt = create_llm_prompt(trajectory, self.goal)
                        result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)
                        score = result["overall_score"]
                    except Exception as e:
                        error_msg = f"Error scoring node {id(current_node)}: {str(e)}"
                        logger.error(error_msg)
                        score = float('-inf')
                    
                    # Update best path if this score is better
                    if score > best_score:
                        best_score = score
                        best_path = path
                            
                    logger.info(f"Node {id(current_node)} score: {score}")
                    
                    # If we've found a satisfactory solution, return it
                    if score >= 0.75:
                        logger.info(f"Found satisfactory solution with score {score}")
                        return [{"action": node.action} for node in path[1:]]
            
            # If we've exhausted all nodes and haven't found a perfect solution,
            # return the best path we found
            if best_path:
                logger.info(f"Returning best path found with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
            
            # If no path was found at all
            logger.warning("No valid path found")
            return []
            
        except Exception as e:
            error_msg = f"Error in BFS search: {str(e)}"
            logger.error(error_msg)
            if best_path:
                logger.info(f"Returning best path found before error with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
            return []

    async def dfs(self) -> List[Dict[str, Any]]:
        """
        Performs depth-first search starting from the root node.
        Skips nodes that are marked as terminal.
        
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        stack = [self.root_node]
        stack_set = {self.root_node}  # Track nodes in stack
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        current_path = []  # Track current path for DFS
        
        try:
            while stack:
                current_node = stack[-1]  # Peek at the top node without removing it
                
                # Skip if we've already visited this node
                if current_node in visited:
                    stack.pop()
                    stack_set.remove(current_node)
                    if current_path:
                        current_path.pop()  # Remove from current path
                    continue
                    
                visited.add(current_node)
                current_path.append(current_node)  # Add to current path
                
                # Skip terminal nodes
                if current_node.is_terminal:
                    logger.info(f"Node {id(current_node)} is terminal")
                    stack.pop()
                    stack_set.remove(current_node)
                    current_path.pop()  # Remove from current path
                    continue
                    
                # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
                if not current_node.children and current_node.depth < self.config.max_depth:
                    try:
                        await self.expand(current_node)
                    except Exception as e:
                        error_msg = f"Error expanding node {id(current_node)}: {str(e)}"
                        logger.error(error_msg)
                        current_node.is_terminal = True
                        stack.pop()
                        stack_set.remove(current_node)
                        current_path.pop()  # Remove from current path
                        continue
                    
                print("print the trajectory")
                print_trajectory(current_node)
                print("print the entire tree")
                print_entire_tree(self.root_node)
                
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
                
                try:
                    # Score the trajectory
                    prompt = create_llm_prompt(trajectory, self.goal)
                    result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)
                    score = result["overall_score"]
                except Exception as e:
                    error_msg = f"Error scoring node {id(current_node)}: {str(e)}"
                    logger.error(error_msg)
                    score = float('-inf')
                
                # Update best path if this score is better
                if score > best_score:
                    best_score = score
                    best_path = path
                        
                logger.info(f"Node {id(current_node)} score: {score}")
                
                # If we've found a satisfactory solution, return it
                if score >= 0.75:
                    logger.info(f"Found satisfactory solution with score {score}")
                    return [{"action": node.action} for node in path[1:]]
                
                # Add non-terminal children to stack in reverse order if they haven't reached max_depth
                has_unvisited_children = False
                for child in reversed(current_node.children):
                    if not child.is_terminal and child not in visited and child not in stack_set and child.depth < self.config.max_depth:
                        stack.append(child)
                        stack_set.add(child)  # Add to stack tracking
                        has_unvisited_children = True
                        break  # Only add one child at a time for DFS
                
                # If no unvisited children, remove current node from stack
                if not has_unvisited_children:
                    stack.pop()
                    stack_set.remove(current_node)
                    current_path.pop()  # Remove from current path
            
            # If we've exhausted all nodes and haven't found a perfect solution,
            # return the best path we found
            if best_path:
                logger.info(f"Returning best path found with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
            
            # If no path was found at all
            logger.warning("No valid path found")
            return []
            
        except Exception as e:
            error_msg = f"Error in DFS search: {str(e)}"
            logger.error(error_msg)
            if best_path:
                logger.info(f"Returning best path found before error with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
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
        queue_set = {self.root_node}  # Track nodes in queue
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        current_level = 0  # Track current level for BFS
        
        try:
            # Get the live browser URL during initial setup
            live_browser_url, session_id = await self._reset_browser(websocket)
            
            # Send initial status if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "search_status",
                    "status": "started",
                    "message": "BFS search started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "live_browser_url": live_browser_url,
                    "session_id": session_id
                })
            
            while queue:
                # Process all nodes at current level
                level_size = len(queue)
                current_level += 1
                level_nodes = []  # Store nodes at current level for later processing
                
                if websocket:
                    await websocket.send_json({
                        "type": "level_start",
                        "level": current_level,
                        "nodes_in_level": level_size,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # First, expand all nodes at current level
                for _ in range(level_size):
                    current_node = queue.popleft()
                    queue_set.remove(current_node)  # Remove from queue tracking
                    
                    # Skip if we've already visited this node
                    if current_node in visited:
                        if websocket:
                            await websocket.send_json({
                                "type": "node_skipped",
                                "node_id": id(current_node),
                                "reason": "already_visited",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        continue
                        
                    visited.add(current_node)
                    
                    # Skip terminal nodes
                    if current_node.is_terminal:
                        if websocket:
                            await websocket.send_json({
                                "type": "node_terminal",
                                "node_id": id(current_node),
                                "reason": "terminal_node",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        continue
                    
                    # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
                    if not current_node.children and current_node.depth < self.config.max_depth:
                        if websocket:
                            await websocket.send_json({
                                "type": "node_expanding",
                                "node_id": id(current_node),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        
                        try:
                            await self.expand(current_node, websocket)
                        except Exception as e:
                            error_msg = f"Error expanding node {id(current_node)}: {str(e)}"
                            logger.error(error_msg)
                            current_node.is_terminal = True
                            if websocket:
                                await websocket.send_json({
                                    "type": "node_error",
                                    "node_id": id(current_node),
                                    "error": error_msg,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            continue
                        
                        # Send tree update after expansion
                        if websocket:
                            tree_data = self._get_tree_data()
                            await websocket.send_json({
                                "type": "tree_update",
                                "tree": tree_data,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    
                    # Store node for later processing
                    level_nodes.append(current_node)
                    
                    # Add non-terminal children to queue for next level if they haven't reached max_depth
                    for child in current_node.children:
                        if not child.is_terminal and child not in visited and child not in queue_set and child.depth < self.config.max_depth:
                            queue.append(child)
                            queue_set.add(child)  # Add to queue tracking
                            
                            # Send queue update if websocket is provided
                            if websocket:
                                await websocket.send_json({
                                    "type": "node_queued",
                                    "node_id": id(child),
                                    "parent_id": id(current_node),
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                
                # Now process all nodes at current level
                for current_node in level_nodes:
                    # Send node processing update if websocket is provided
                    if websocket:
                        await websocket.send_json({
                            "type": "node_processing",
                            "node_id": id(current_node),
                            "depth": current_node.depth,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    print("print the trajectory")
                    print_trajectory(current_node)
                    print("print the entire tree")
                    print_entire_tree(self.root_node)
                    
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
                    
                    try:
                        # Score the trajectory
                        prompt = create_llm_prompt(trajectory, self.goal)
                        result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)
                        score = result["overall_score"]
                    except Exception as e:
                        error_msg = f"Error scoring node {id(current_node)}: {str(e)}"
                        logger.error(error_msg)
                        score = float('-inf')
                        if websocket:
                            await websocket.send_json({
                                "type": "node_error",
                                "node_id": id(current_node),
                                "error": error_msg,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    
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
                        
                    logger.info(f"Node {id(current_node)} score: {score}")
                    
                    # If we've found a satisfactory solution, return it
                    if score >= 0.75:
                        logger.info(f"Found satisfactory solution with score {score}")
                        
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
                
                if websocket:
                    await websocket.send_json({
                        "type": "level_complete",
                        "level": current_level,
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
            
        except Exception as e:
            error_msg = f"Error in BFS search: {str(e)}"
            logger.error(error_msg)
            if websocket:
                await websocket.send_json({
                    "type": "search_error",
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
            if best_path:
                logger.info(f"Returning best path found before error with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
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
        stack_set = {self.root_node}  # Track nodes in stack
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        current_path = []  # Track current path for DFS
        
        try:
            # Get the live browser URL during initial setup
            live_browser_url, session_id = await self._reset_browser(websocket)
            
            # Send initial status if websocket is provided
            if websocket:
                await websocket.send_json({
                    "type": "search_status",
                    "status": "started",
                    "message": "DFS search started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "live_browser_url": live_browser_url,
                    "session_id": session_id
                })
            
            while stack:
                current_node = stack[-1]  # Peek at the top node without removing it
                
                # Skip if we've already visited this node
                if current_node in visited:
                    stack.pop()
                    stack_set.remove(current_node)
                    if current_path:
                        current_path.pop()  # Remove from current path
                    if websocket:
                        await websocket.send_json({
                            "type": "node_backtrack",
                            "node_id": id(current_node),
                            "reason": "already_visited",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    continue
                    
                visited.add(current_node)
                current_path.append(current_node)  # Add to current path
                
                # Skip terminal nodes
                if current_node.is_terminal:
                    logger.info(f"Node {id(current_node)} is terminal")
                    stack.pop()
                    stack_set.remove(current_node)
                    current_path.pop()  # Remove from current path
                    if websocket:
                        await websocket.send_json({
                            "type": "node_backtrack",
                            "node_id": id(current_node),
                            "reason": "terminal_node",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    continue
                    
                # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
                if not current_node.children and current_node.depth < self.config.max_depth:
                    if websocket:
                        await websocket.send_json({
                            "type": "node_expanding",
                            "node_id": id(current_node),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    try:
                        await self.expand(current_node, websocket)
                    except Exception as e:
                        error_msg = f"Error expanding node {id(current_node)}: {str(e)}"
                        logger.error(error_msg)
                        current_node.is_terminal = True
                        stack.pop()
                        stack_set.remove(current_node)
                        current_path.pop()  # Remove from current path
                        if websocket:
                            await websocket.send_json({
                                "type": "node_backtrack",
                                "node_id": id(current_node),
                                "reason": "expansion_error",
                                "error": error_msg,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        continue
                    
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
                
                try:
                    # Score the trajectory
                    prompt = create_llm_prompt(trajectory, self.goal)
                    result = score_trajectory_with_openai(prompt, openai_client, model=self.config.evaluation_model)
                    score = result["overall_score"]
                except Exception as e:
                    error_msg = f"Error scoring node {id(current_node)}: {str(e)}"
                    logger.error(error_msg)
                    score = float('-inf')
                    if websocket:
                        await websocket.send_json({
                            "type": "node_error",
                            "node_id": id(current_node),
                            "error": error_msg,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
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
                    
                logger.info(f"Node {id(current_node)} score: {score}")
                
                # If we've found a satisfactory solution, return it
                if score >= 0.75:
                    logger.info(f"Found satisfactory solution with score {score}")
                    
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
                has_unvisited_children = False
                for child in reversed(current_node.children):
                    if not child.is_terminal and child not in visited and child not in stack_set:
                        stack.append(child)
                        stack_set.add(child)  # Add to stack tracking
                        has_unvisited_children = True
                        
                        # Send stack update if websocket is provided
                        if websocket:
                            await websocket.send_json({
                                "type": "node_stacked",
                                "node_id": id(child),
                                "parent_id": id(current_node),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        break  # Only add one child at a time for DFS
                
                # If no unvisited children, remove current node from stack
                if not has_unvisited_children:
                    stack.pop()
                    stack_set.remove(current_node)
                    current_path.pop()  # Remove from current path
                    if websocket:
                        await websocket.send_json({
                            "type": "node_backtrack",
                            "node_id": id(current_node),
                            "reason": "no_unvisited_children",
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
            
        except Exception as e:
            error_msg = f"Error in DFS search: {str(e)}"
            logger.error(error_msg)
            if websocket:
                await websocket.send_json({
                    "type": "search_error",
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
            if best_path:
                logger.info(f"Returning best path found before error with score {best_score}")
                return [{"action": node.action} for node in best_path[1:]]
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

    async def rmcts(self) -> List[Dict[str, Any]]:
        """
        Performs Monte Carlo Tree Search starting from the root node.
        Uses GPT-4 for node selection and reflection-based backpropagation.
        
        Returns:
            List[Dict[str, Any]]: List of actions in the best path found
        """
        best_score = float('-inf')
        best_path = None
        visited = set()  # Track visited nodes to avoid cycles
        max_iterations = self.config.iterations  # Use configured number of iterations
        
        try:
            # Initial browser setup
            live_browser_url, session_id = await self._reset_browser()
            if not live_browser_url:
                logger.error("Failed to initialize browser")
                return []
                
            for iteration in range(max_iterations):
                logger.info(f"\n{'='*50}")
                logger.info(f"RMCTS Iteration {iteration + 1}/{max_iterations}")
                logger.info(f"{'='*50}\n")
                
                # Selection: Use GPT-4 to select a promising path
                current_node = self.root_node
                path = [current_node]
                selection_depth = 0
                
                while current_node.children and not current_node.is_terminal:
                    logger.info(f"\nSelection Step {selection_depth + 1}:")
                    logger.info(f"Current node action: {current_node.action}")
                    logger.info(f"Number of children: {len(current_node.children)}")
                    
                    # Get trajectory for GPT-4 to evaluate
                    trajectory = []
                    for node in path[1:]:  # Skip root node
                        trajectory.append({
                            "natural_language_description": node.natural_language_description,
                            "action": node.action,
                            "feedback": node.feedback
                        })
                    
                    # Create prompt for GPT-4 to select next node
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
                        'value': child.value
                    } for child in current_node.children], indent=2)}
                    
                    Return a JSON response with:
                    {{
                        "selected_child_index": int,  # Index of the selected child
                        "explanation": str  # Brief explanation of the selection
                    }}"""
                    
                    try:
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
                            
                    except Exception as e:
                        logger.error(f"Error in node selection: {str(e)}")
                        break
                    
                    selection_depth += 1
                
                # Expansion: Expand the selected node if possible
                if not current_node.is_terminal and current_node.depth < self.config.max_depth:
                    logger.info(f"\nExpansion Step:")
                    logger.info(f"Expanding node: {current_node.action}")
                    try:
                        await self.expand(current_node)
                        logger.info(f"Successfully expanded node with {len(current_node.children)} children")
                    except Exception as e:
                        logger.error(f"Error expanding node: {str(e)}")
                        current_node.is_terminal = True
                
                # Simulation: Evaluate the current path
                logger.info(f"\nSimulation Step:")
                logger.info(f"Evaluating path of length {len(path) - 1}")
                try:
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
                    
                    logger.info(f"Simulation Results:")
                    logger.info(f"Overall Score: {score:.3f}")
                    logger.info(f"Efficiency Score: {result['efficiency_score']:.3f}")
                    logger.info(f"Accuracy Score: {result['accuracy_score']:.3f}")
                    logger.info(f"Robustness Score: {result['robustness_score']:.3f}")
                    
                    # Update best path if this score is better
                    if score > best_score:
                        best_score = score
                        best_path = path
                        logger.info(f"\nNew best path found!")
                        logger.info(f"Previous best score: {best_score:.3f}")
                        logger.info(f"New best score: {score:.3f}")
                    
                    # Reflection-based backpropagation
                    if score < 0.75:  # If the path is not satisfactory
                        logger.info(f"\nReflection Step (Score {score:.3f} < 0.75):")
                        # Generate reflection prompt
                        reflection_prompt = f"""Analyze the current trajectory and suggest improvements.
                        
                        Goal: {self.goal}
                        
                        Current Trajectory:
                        {json.dumps(trajectory, indent=2)}
                        
                        Score: {score}
                        
                        Return a JSON response with:
                        {{
                            "backtrack_to_step": int,  # Which step to backtrack to (0-based index)
                            "reason": str,  # Why backtrack to this step
                            "suggested_improvements": [str]  # List of suggested improvements
                        }}"""
                        
                        try:
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
                                current_node = path[backtrack_step]
                                # Remove nodes after the backtrack point
                                while len(path) > backtrack_step + 1:
                                    path.pop()
                                logger.info(f"Backtracking to step {backtrack_step}")
                                logger.info(f"Reason: {reflection_result['reason']}")
                                logger.info("Suggested improvements:")
                                for improvement in reflection_result["suggested_improvements"]:
                                    logger.info(f"- {improvement}")
                                
                        except Exception as e:
                            logger.error(f"Error in reflection: {str(e)}")
                    
                    # If we've found a satisfactory solution, return it
                    if score >= 0.75:
                        logger.info(f"\nFound satisfactory solution with score {score:.3f}")
                        return [{"action": node.action} for node in path[1:]]
                    
                except Exception as e:
                    logger.error(f"Error in simulation: {str(e)}")
                    continue
                
                # Update node statistics
                logger.info(f"\nBackpropagation Step:")
                for node in path:
                    old_value = node.value
                    node.visits += 1
                    node.value = (node.value * (node.visits - 1) + score) / node.visits
                    logger.info(f"Node {node.action}:")
                    logger.info(f"  Visits: {node.visits}")
                    logger.info(f"  Value: {old_value:.3f} -> {node.value:.3f}")
            
            # If we've exhausted all iterations and haven't found a perfect solution,
            # return the best path we found
            if best_path:
                logger.info(f"\nSearch complete. Returning best path found with score {best_score:.3f}")
                return [{"action": node.action} for node in best_path[1:]]
            
            # If no path was found at all
            logger.warning("\nNo valid path found")
            return []
            
        except Exception as e:
            error_msg = f"Error in RMCTS search: {str(e)}"
            logger.error(error_msg)
            if best_path:
                logger.info(f"\nReturning best path found before error with score {best_score:.3f}")
                return [{"action": node.action} for node in best_path[1:]]
            return []

