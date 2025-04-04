"""Language-based Action Tree Search (LATS) Agent implementation."""

import time
from typing import Any, Optional, Tuple, List
import os
from openai import OpenAI
from datetime import datetime
import aiohttp
from dotenv import load_dotenv
load_dotenv()

from .lats_node import LATSNode, Observation
from ...core_async.config import AgentConfig

from ...webagent_utils_async.action.highlevel import HighLevelActionSet
from ...webagent_utils_async.utils.playwright_manager import AsyncPlaywrightManager, setup_playwright
from .tree_vis import RED, better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...replay_async import generate_feedback, playwright_step_execution, locate_element_from_action
from ...webagent_utils_async.browser_env.observation import extract_page_info, observe_features
from ...webagent_utils_async.action.prompt_functions import generate_actions_with_observation
from ...webagent_utils_async.evaluation.feedback import generate_feedback_with_screenshot
from ...webagent_utils_async.utils.utils import urls_to_images


from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation_async.evaluators import goal_finished_evaluator
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.browser_env.observation import extract_page_info
from .lats_node import LATSNode
from .tree_vis import better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...webagent_utils_async.action.utils import execute_action
from ...webagent_utils_async.action.prompt_functions import extract_top_actions, is_goal_finished
from ...webagent_utils_async.browser_env.observation import extract_page_info
from ...webagent_utils_async.evaluation.feedback import capture_post_action_feedback

openai_client = OpenAI()

class LATSAgent:
    """
    Language-based Action Tree Search Agent implementation.
    
    This agent uses MCTS-like tree search to find optimal action sequences for web navigation tasks.
    
    Attributes:
        starting_url (str): The initial URL to start from
        model_name (str): Name of the language model to use
        goal (str): The goal state to achieve
        playwright_manager (PlaywrightManager): Manager for browser automation
        num_simulations (int): Number of simulations to run
        exploration_weight (float): Exploration vs exploitation trade-off parameter
    """
    
    def __init__(
        self,
        starting_url: str,
        messages: list[dict[str, Any]],
        goal: str,
        images: list,
        playwright_manager: AsyncPlaywrightManager,
        config: AgentConfig,
    ):
        """Initialize the LATS Agent."""
        # no action grounding model, just one step to geneate both action natural language description and action at the same time
        self.starting_url = starting_url
        self.goal = goal
        self.image_urls = images
        self.images = urls_to_images(self.image_urls)

        self.messages = messages
        if len(images) == 0:
            self.messages.append({"role": "user", "content": f"The goal is: {self.goal}"})
        else:
            self.messages.append({"role": "user", "content": f"The goal is: {self.goal}"})

        self.playwright_manager = playwright_manager

        self.config = config

        # set bid, only click, fill, hoover, drag and draw
        self.agent_type = ["bid"]
        self.action_set = HighLevelActionSet(
            subsets=self.agent_type, strict=False, multiaction=False, demo_mode="default"
        )
        self.root_node = LATSNode(
            natural_language_description=None,
            action=None,
            prob=None,
            element=None,
            goal=self.goal,
            parent=None
        )
        self.goal_finished = False
        self.result_node = None
        self.reset_url = os.environ["ACCOUNT_RESET_URL"]

    async def run(self, websocket=None) -> list[LATSNode]:
        """
        Run the LATS search and return the best path found.
        
        Args:
            websocket: Optional WebSocket connection for sending updates
            
        Returns:
            list[LATSNode]: Best path from root to terminal node
        """
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "Starting LATS search",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        best_node = await self.lats_search(websocket)
        print_trajectory(best_node)
        
        if websocket:
            await websocket.send_json({
                "type": "search_complete",
                "status": "success" if best_node.reward == 1 else "partial_success",
                "score": best_node.reward,
                "path": [{"id": id(node), "action": node.action} for node in best_node.get_trajectory()],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return best_node.get_trajectory()

    async def lats_search(self, websocket=None) -> LATSNode:
        """
        Perform the main LATS search algorithm.
        
        Args:
            websocket: Optional WebSocket connection for sending updates
            
        Returns:
            LATSNode: Best terminal node found
        """        
        print(f"")
        print(f"{GREEN}START SEARCH{RESET}")

        terminal_nodes = []

        for i in range(self.config.iterations):
            if websocket:
                await websocket.send_json({
                    "type": "iteration_start",
                    "iteration": i + 1,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            print(f"")
            print(f"")
            print(f"Iteration {i + 1}...")
            
            # Step 1: Selection with websocket update
            if websocket:
                await websocket.send_json({
                    "type": "step_start",
                    "step": "selection",
                    "iteration": i + 1,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            node = self.select_node(self.root_node)

            if node is None:
                print("All paths lead to terminal nodes with reward 0. Ending search.")
                break

            print(f"{GREEN}Tree:{RESET}")
            better_print(node=self.root_node, selected_node=node)
            print(f"")

            # Step 2: Expansion with websocket update
            if websocket:
                await websocket.send_json({
                    "type": "step_start",
                    "step": "expansion",
                    "iteration": i + 1,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            await self.expand_node(node, websocket)

            while node is not None and node.is_terminal and not self.goal_finished:
                print(f"Depth limit node found at iteration {i + 1}, reselecting...")
                node = self.select_node(self.root_node)
                if node is not None:
                    await self.expand_node(node, websocket)

            if node is None:
                # all the nodes are terminal, stop the search
                print(f"{RED}All nodes are terminal, stopping search{RESET}")
                break

            if self.goal_finished:
                print(f"{RED}Goal finished, stopping search{RESET}")
                break
            
            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

            # Step 3: Evaluation
            print(f"")
            print(f"{GREEN}Step 3: evaluation{RESET}")
            await self.evaluate_node(node)

            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

            # Step 4: Simulation
            print(f"{GREEN}Step 4: simulation{RESET}")
            # # Find the child with the highest value
            ## always = 1
            reward, terminal_node = await self.simulate(max(node.children, key=lambda child: child.value), max_depth=self.config.max_depth, num_simulations=1)
            terminal_nodes.append(terminal_node)

            if reward == 1:
                return terminal_node

            # Step 5: Backpropagation
            print(f"{GREEN}Step 5: backpropagation{RESET}")
            self.backpropagate(terminal_node, reward)
            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

            # Send tree update after each iteration
            if websocket:
                tree_data = self._get_tree_data()
                await websocket.send_json({
                    "type": "tree_update",
                    "tree": tree_data,
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Find best node
        all_nodes_list = collect_all_nodes(self.root_node)
        all_nodes_list.extend(terminal_nodes)
        
        ## temp change: if reward is the same, choose the deeper node
        best_child = max(all_nodes_list, key=lambda x: (x.reward, x.depth))
        
        if best_child.reward == 1:
            print("Successful trajectory found")
        else:
            print("Unsuccessful trajectory found")
        await self.playwright_manager.close()
            
        return best_child if best_child is not None else self.root_node

    def select_node(self, node: LATSNode) -> Optional[LATSNode]:
        """
        Select a node for expansion using UCT.
        
        Args:
            node: Root node to start selection from
            
        Returns:
            Optional[LATSNode]: Selected node or None if all paths exhausted
        """        
        if node.is_terminal:
            return None
        return node.get_best_leaf()

    async def expand_node(self, node: LATSNode, websocket=None) -> None:
        """
        Expand a node by generating its children.
        
        Args:
            node: Node to expand
            websocket: Optional WebSocket connection for sending updates
        """
        if websocket:
            await websocket.send_json({
                "type": "node_expanding",
                "node_id": id(node),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        children = await self.generate_children(node, websocket)

        for child in children:
            node.add_child(child)
            if websocket:
                await websocket.send_json({
                    "type": "node_created",
                    "node_id": id(child),
                    "parent_id": id(node),
                    "action": child.action,
                    "description": child.natural_language_description,
                    "timestamp": datetime.utcnow().isoformat()
                })

        if children and children[0].goal_finish_feedback.is_done:
            self.set_goal_finished(children[0])
            if websocket:
                await websocket.send_json({
                    "type": "goal_finished",
                    "node_id": id(children[0]),
                    "timestamp": datetime.utcnow().isoformat()
                })
            return
        
        node.check_terminal()

    async def evaluate_node(self, node: LATSNode) -> None:
        """
        Evaluate a node using LLM scoring.
        
        Args:
            node: Node to evaluate
            
        Returns:
            float: Evaluation score
        """
        scores = []
        print(f"{GREEN}-- total {len(node.children)} children to evaluate:{RESET}")
        for i, child in enumerate(node.children):
            print(f"{GREEN}--- evaluating child {i+1}...{RESET}")
            if child.is_terminal:
                score = 0
            else:
                trajectory = child.get_trajectory()
                prompt = create_llm_prompt(trajectory, self.goal)
                result = score_trajectory_with_openai(prompt, openai_client, self.config.evaluation_model, child.observation.image)
                score = result["overall_score"]
            scores.append(score)

        for child, score in zip(node.children, scores):
            child.value = score
            child.reward = score

    async def simulate(self, node: LATSNode, max_depth: int = 2, num_simulations=1) -> tuple[float, LATSNode]:
        """
        Perform a rollout simulation from a node.
        
        Args:
            node: Starting node for rollout
            max_depth: Maximum depth to simulate to
            
        Returns:
            tuple[float, LATSNode]: (Score of the rollout, Terminal node reached)
        """
        depth = node.depth
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)
        return await self.rollout(node, max_depth=max_depth)
    
    async def send_completion_request(self, plan, depth, node, trajectory=[]):
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)

        if depth >= self.config.max_depth:
            return trajectory, node

        context = await self.playwright_manager.get_context()
        page = await self.playwright_manager.get_page()
        # Extract page information
        time.sleep(3)
        page_info = await extract_page_info(page, fullpage=True, log_folder=self.config.log_folder)
        updated_actions = await extract_top_actions(
            trajectory, self.goal, self.images, page_info, self.action_set, openai_client,
            features=["axtree"], elements_filter="som", branching_factor=self.config.branching_factor,
            log_folder=self.config.log_folder, fullpage=True,
            action_generation_model=self.config.action_generation_model,
            action_grounding_model=self.config.action_grounding_model
        )
        next_action = updated_actions[0]
        retry_count = self.config.retry_count if hasattr(self.config, 'retry_count') else 1  # Default retries if not set
        
        for attempt in range(retry_count):
            try:
                # Convert action to Python code
                code, function_calls = self.action_set.to_python_code(next_action["action"])

                # Locate element
                if len(function_calls) == 1:
                    for function_name, function_args in function_calls:
                        extracted_number = parse_function_args(function_args)
                        element = await locate_element(page, extracted_number)
                        next_action["element"] = element
                
                # Execute action
                await execute_action(next_action, self.action_set, page, context, self.goal, page_info['interactive_elements'],
                            self.config.log_folder)
                feedback = await capture_post_action_feedback(page, next_action, self.goal, self.config.log_folder)
                trajectory.append({'action': next_action['action'], 'feedback': feedback})
                action_str = next_action["action"]

                print(f"The action is: {action_str} - The action result is: {feedback}")

                # Check if goal is finished
                messages = [{"role": "system", "content": "The goal is {}, Is the overall goal finished?".format(self.goal)}]
                for item in trajectory:
                    action = item['action']
                    feedback = item['feedback']
                    messages.append({"role": "user", "content": 'action is: {}'.format(action)})
                    messages.append({"role": "user", "content": 'action feedback is: {}'.format(feedback)})

                goal_finished = await is_goal_finished(messages, openai_client)

                new_node = LATSNode(
                    natural_language_description=next_action["natural_language_description"],
                    action=next_action["action"],
                    prob=next_action["prob"],
                    element=next_action["element"],
                    goal=node.goal,
                    parent=node
                )

                if goal_finished:
                    return trajectory, new_node

                return await self.send_completion_request(plan, depth + 1, new_node, trajectory)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt + 1 == retry_count:
                    print("Max retries reached. Skipping this step and retrying the whole request.")
                    # Retry the entire request from the same state
                    return await self.send_completion_request(plan, depth, node, trajectory)

        # If all retries and retries of retries fail, return the current trajectory and node
        return trajectory, node

    
    async def rollout(self, node: LATSNode, max_depth: int = 2)-> tuple[float, LATSNode]:
        # Reset browser state
        await self._reset_browser()
        path = self.get_path_to_root(node)
        
        print("execute path")
        # Execute path

        messages = []
        trajectory = []
  
        for n in path[1:]:  # Skip root node
            success = await playwright_step_execution(
                n, 
                self.goal, 
                self.playwright_manager, 
                is_replay=False, 
                log_folder=self.config.log_folder
            )
            if not success:
                return 0, n
            if not n.feedback:
                n.feedback = await generate_feedback(
                    self.goal,
                    n.natural_language_description,
                    self.playwright_manager,
                )
                trajectory.append({
                    "action": n.action,
                    "feedback": n.feedback
                })
        ## call the prompt agent
        print("current depth: ", len(path) - 1)
        print("max depth: ", self.config.max_depth)
        trajectory, node = await self.send_completion_request(self.goal, len(path) - 1, node=n, trajectory=trajectory)
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)

        page = await self.playwright_manager.get_page()
        page_info = await extract_page_info(page, self.config.fullpage, self.config.log_folder)

        messages = [{"role": "user", "content": f"Action is: {n.action}"} for n in path[1:]]
        goal_finished, confidence_score = goal_finished_evaluator(
            messages, 
            openai_client, 
            self.goal, 
            page_info['screenshot']
        )
        print("evaluating")
        
        score = confidence_score if goal_finished else 0

        return score, node

    def backpropagate(self, node: LATSNode, value: float) -> None:
        """
        Backpropagate values through the tree.
        
        Args:
            node: Current node to start backpropagation from
            value: Value to propagate upwards
        """
        while node:
            node.visits += 1
            node.value = (node.value * (node.visits - 1) + value) / node.visits
            node = node.parent

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

    async def observe(self) -> None:
        page = await self.playwright_manager.get_page()
        page_info = await extract_page_info(page, self.config.fullpage, self.config.log_folder)
        feature_text = await observe_features(
            page_info, 
            features=self.config.features,
            elements_filter=self.config.elements_filter,
            log_folder=self.config.log_folder,
            fullpage=self.config.fullpage
        )
        screenshot = page_info['screenshot_som']
        observation = Observation(
            text=feature_text,
            image=screenshot,
        )
        return observation

    async def execute_action_trajectory(self, action_trajectory: list[dict]) -> None:
        if not action_trajectory:
            return True

        await self._reset_browser()
        print("taking action trajectory")
        for action_data in action_trajectory:
            print("action_data")
            print(action_data)
            
            # Convert action_data dict to LATSNode
            temp_node = LATSNode(
                natural_language_description=action_data["natural_language_description"],
                action=action_data["action"],
                prob=0,
                element=action_data["element"],
                goal=self.goal,
                parent=None  # No parent needed for temporary node
            )
            
            success = await playwright_step_execution(
                temp_node,  # Pass the node instead of raw action_data
                self.goal,
                self.playwright_manager,
                is_replay=False,
                log_folder=self.config.log_folder
            )
            
            if not success:
                return False
        return True

    async def generate_candidate_actions(self, node: LATSNode) -> list[dict]:
        trajectory = node.get_trajectory()
        action_trajectory = node.get_action_trajectory()
        await self.execute_action_trajectory(action_trajectory)
        observation = await self.observe()
        # only root node has no observation at this point
        if node.observation is None:
            node.observation = observation
        actions = await generate_actions_with_observation(
            trajectory,
            self.goal,
            self.images,
            openai_client=openai_client,
            action_set=self.action_set,
            feature_text=observation.text,
            screenshot=observation.image,
            branching_factor=self.config.branching_factor,
            log_folder=self.config.log_folder,
            action_generation_model=self.config.action_generation_model,
        )

        page = await self.playwright_manager.get_page()
        valid_actions = []
        for action_data in actions:
            if action_data["action"] == "FINISH":
                continue

            is_bid_action, element_data = await locate_element_from_action(page, action_data["action"])
            if is_bid_action and not element_data:
                continue

            action_data['element'] = element_data
            valid_actions.append(action_data)
        return valid_actions

    async def generate_children(self, node: LATSNode, websocket=None) -> list[LATSNode]:
        print(f"{GREEN}-- generating candidate actions...{RESET}")

        children = []
        
        action_trajectory = node.get_action_trajectory()
        candidate_actions = await self.generate_candidate_actions(node)
        print(f"{GREEN}-- generated {len(candidate_actions)} actions{RESET}")
        for action_data in candidate_actions:
            print(f"{GREEN}--- {action_data['action']}{RESET}")
            print(f"{GREEN}--- {action_data['natural_language_description']}{RESET}")

        print(f"")
        print(f"{GREEN}-- executing candidate trajectories{RESET}")
        for i, action_data in enumerate(candidate_actions):

            candidate_action_trajectory = action_trajectory + [action_data]
            print(f"{GREEN}--- trajectory {i+1}:{RESET}")
            for action in candidate_action_trajectory:
                print(f"{GREEN}---- {action['action']}{RESET}")
                print(f"{GREEN}---- {action['natural_language_description']}{RESET}")
            executed_successfully = await self.execute_action_trajectory(candidate_action_trajectory)
            if not executed_successfully:
                # not executed successfully, give up this candidate
                print(f"{RED}--- failed to execute action trajectory{RESET}")
                continue

            observation = await self.observe()
            print(f"{GREEN}--- generate feedback...{RESET}")
            feedback = await generate_feedback_with_screenshot(
                self.goal,
                action_data["natural_language_description"],
                observation.image,
                model=self.config.feedback_model,
            )
            print(f"feedback: is_done: {feedback.is_done}, explanation: {feedback.explanation}")

            child = LATSNode(
                natural_language_description=action_data["natural_language_description"],
                action=action_data["action"],
                prob=action_data["prob"],
                element=action_data["element"],
                goal=node.goal,
            )
            child.observation = observation
            child.goal_finish_feedback = feedback
            if feedback.is_done:
                # the goal is finished, stop the search
                return [child]
            
            children.append(child)

            if node.depth + 1 >= self.config.max_depth:
                child.is_terminal = True
        
        return children

    def set_goal_finished(self, node: LATSNode) -> None:
        self.goal_finished = True
        self.result_node = node

    def get_path_to_root(self, node: LATSNode) -> List[LATSNode]:
        path = []
        current = node
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

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
                "is_terminal": node.is_terminal,
                "value": node.value,
                "visits": node.visits,
                "reward": node.reward
            }
            tree_data.append(node_data)
        
        return tree_data
