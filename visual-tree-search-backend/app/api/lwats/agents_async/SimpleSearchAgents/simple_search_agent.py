import logging
import time
from typing import Any, Dict, List, Optional
from collections import deque

from openai import OpenAI

from ...core.config import AgentConfig

from ...webagent_utils_async.action.highlevel import HighLevelActionSet
from ...webagent_utils_async.utils.playwright_manager import AsyncPlaywrightManager, setup_playwright
from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation.evaluators import goal_finished_evaluator
from ...replay_async import generate_feedback, playwright_step_execution
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.browser_env.observation import extract_page_info
from .lats_node import LATSNode
from .tree_vis import better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...webagent_utils_sync.utils.utils import urls_to_images

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

    async def run(self) -> List[Dict[str, Any]]:
        if self.config.search_algorithm == "bfs":
            logger.info("Starting BFS algorithm")
            return await self.bfs()
        else:
            logger.info("Starting DFS algorithm")
            return await self.dfs()

    async def _reset_browser(self) -> None:
        """Reset the browser to initial state."""
        await self.playwright_manager.close()
        self.playwright_manager = await setup_playwright(
            storage_state=self.config.storage_state,
            headless=self.config.headless,
            mode=self.config.browser_mode
        )
        page = await self.playwright_manager.get_page()
        await page.goto(self.starting_url, wait_until="networkidle")
    
    # def expand(self, node: LATSNode, finished_score_threshold: float = 0.9) -> bool:
    
    async def expand(self, node: LATSNode) -> None:
        """
        Expand a node by generating its children.
        
        Args:
            node: Node to expand
        """
        if node.depth >= 7:
            logger.info("Depth limit reached")
            node.is_terminal = True
            return
            
        children_state = await self.generate_children(node)
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

    async def generate_children(self, node: LATSNode) -> list[dict]:
        """
        Generate child nodes for a given node.
        
        Args:
            node: Parent node to generate children for
            
        Returns:
            list[dict]: List of child state dictionaries
        """
        await self._reset_browser()
        path = self.get_path_to_root(node)
        
        # Execute path
        for n in path[1:]:  # Skip root node
            success = await playwright_step_execution(
                n,
                self.goal,
                self.playwright_manager,
                is_replay=False,
                log_folder=self.config.log_folder
            )
            if not success:
                n.is_terminal = True
                return []
            
            if not n.feedback:
                n.feedback = await generate_feedback(
                    self.goal,
                    n.natural_language_description,
                    self.playwright_manager,
                )

        time.sleep(3)
        page = await self.playwright_manager.get_page()
        page_info = await extract_page_info(page, self.config.fullpage, self.config.log_folder)

        messages = [{"role": "user", "content": f"Action is: {n.action}"} for n in path[1:]]
        
        ## TODO: add feedback as well?
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
                    return []
                continue
                
            page = await self.playwright_manager.get_page()
            # page_info = extract_page_info(page, self.fullpage, self.log_folder)
            code, function_calls = self.action_set.to_python_code(action["action"])

            if len(function_calls) == 1:
                try:
                    for function_name, function_args in function_calls:
                        extracted_number = parse_function_args(function_args)
                        element = await locate_element(page, extracted_number)
                        action["element"] = element
                except Exception:
                    action["element"] = None
                children.append(action)

        if not children:
            node.is_terminal = True
            
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

            score = result["score"]
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = path
                    
            logger.info(f"Node score: {score}")
            
            # If we've found a satisfactory solution, return it
            if score >= 9:
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

            score = result["score"]
            
            logger.info(f"Node score: {score}")
            
            return score, score >= 9
        
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