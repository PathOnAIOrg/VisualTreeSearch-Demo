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


class BaseAgent:    
    # no need to pass an initial playwright_manager to the agent class
    def __init__(
        self,
        starting_url: str,
        messages: list[dict[str, Any]],
        goal: str,
        images: list,
        playwright_manager: AsyncPlaywrightManager,
        config: AgentConfig,
    ):
        # no action grounding model, just one step to geneate both action natural language description and action at the same time
        self.starting_url = starting_url
        self.goal = goal
        self.image_urls = images
        self.images = urls_to_images(self.image_urls)

        ## TODO: check whether self.messages are needed
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
            natural_language_description="Root Node",
            action="ROOT",
            prob=1.0,
            element=None,
            goal=self.goal,
            parent=None
        )
        self.root_node.value = 0.0
        self.root_node.visits = 0
        self.root_node.depth = 0
        self.root_node.is_terminal = False
        self.goal_finished = False
        self.result_node = None
        self.reset_url = os.environ["ACCOUNT_RESET_URL"]

    def get_path_to_root(self, node: LATSNode) -> List[LATSNode]:
        path = []
        current = node
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    def _get_tree_data(self):
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
                "feedback": node.feedback,
                # "reward": node.reward
            }
            tree_data.append(node_data)
        
        return tree_data
    
    ## TODO: newly added, debug needed
    async def remove_simulated_trajectory(self, starting_node, terminal_node: LATSNode, websocket=None):
        # to be implemented
        trajectory_data = []
        path = []
        
        # Collect path from terminal to root
        current = terminal_node
        while current is not starting_node:
            path.append(current)
            current = current.parent
            
        # Process nodes in order from root to terminal
        for level, node in enumerate(reversed(path)):
            node_data = {
                "id": id(node),
                "level": level,
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description,
                "visits": node.visits,
                "value": float(f"{node.value:.3f}") if hasattr(node, 'value') else None,
                # "reward": float(f"{node.reward:.3f}") if hasattr(node, 'reward') else None,
                "is_terminal": node.is_terminal,
                "feedback": node.feedback if hasattr(node, 'feedback') else None,
                "is_root": not hasattr(node, 'parent') or node.parent is None,
                "is_terminal_node": node == terminal_node
            }
            trajectory_data.append(node_data)
        
        await self.websocket_simulation_removed(trajectory_data, websocket=websocket)
        pass
    
    def _get_trajectory_data(self, terminal_node: LATSNode):
        trajectory_data = []
        path = []
        
        # Collect path from terminal to root
        current = terminal_node
        while current is not None:
            path.append(current)
            current = current.parent
            
        # Process nodes in order from root to terminal
        for level, node in enumerate(reversed(path)):
            node_data = {
                "id": id(node),
                "level": level,
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description,
                "visits": node.visits,
                "value": float(f"{node.value:.3f}") if hasattr(node, 'value') else None,
                # "reward": float(f"{node.reward:.3f}") if hasattr(node, 'reward') else None,
                "is_terminal": node.is_terminal,
                "feedback": node.feedback if hasattr(node, 'feedback') else None,
                "is_root": not hasattr(node, 'parent') or node.parent is None,
                "is_terminal_node": node == terminal_node
            }
            trajectory_data.append(node_data)
            
        return trajectory_data 


    async def _reset_browser(self, websocket=None) -> Optional[str]:
        await self.playwright_manager.close()
        
        ## reset account using api-based account reset
        if self.config.account_reset:            
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
    
    # TODO: if no websocket, print the json data
    # TODO: do we need node expansion data?
    # TODO: four types of websocket messages, do we need more type of websocket messages?
    async def websocket_iteration_start(self, iteration, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "iteration_start",
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def websocket_step_start(self, step, step_name, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "step_start",
                "step": step,
                "step_name": step_name,
                "timestamp": datetime.utcnow().isoformat()
            })

    # node selected is used to highlight node
    async def websocket_node_selection(self, node, websocket=None, type="node_selected"):
        if websocket:
            await websocket.send_json({
                "type":type,
                "node_id": id(node),
                "parent_id": id(node.parent),
                "action": node.action,
                "description": node.natural_language_description,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            print(f"{type}: {GREEN}{id(node)}{RESET}")
            print(f"Node parent: {GREEN}{id(node.parent)}{RESET}")
            print(f"Node action: {GREEN}{node.action}{RESET}")
            print(f"Node description: {GREEN}{node.natural_language_description}{RESET}")

    async def websocket_tree_update(self, type, tree_data, websocket=None):
        if websocket:
            await websocket.send_json({
                        "type": type,
                        "tree": tree_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
        else:
            print(f"{type} updated: {tree_data}")
    
    async def websocket_node_created(self, child, node, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "node_created",
                "node_id": id(child),
                "parent_id": id(node),
                "action": child.action,
                "description": child.natural_language_description,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            print(f"Node created: {GREEN}{id(child)}{RESET}")
            print(f"Node parent: {GREEN}{id(node)}{RESET}")
            print(f"Node action: {GREEN}{child.action}{RESET}")
            print(f"Node description: {GREEN}{child.natural_language_description}{RESET}")
    
    ## node simulated
    ## message log and d3 visualization add different information
    async def websocket_node_simulated(self, child, node, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "node_simulated",
                "node_id": id(child),
                "parent_id": id(node),
                "action": child.action,
                "description": child.natural_language_description,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            print(f"Node simulated: {GREEN}{id(child)}{RESET}")
            print(f"Node parent: {GREEN}{id(node)}{RESET}")
            print(f"Node action: {GREEN}{child.action}{RESET}")
            print(f"Node description: {GREEN}{child.natural_language_description}{RESET}")
        ## but different color for the link

    async def websocket_simulation_removed(self, trajectory, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "removed_simulation",
                "trajectory": trajectory,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            print(f"Simulation removed: {GREEN}{trajectory}{RESET}")

    async def websocket_simulation_result(self, reward, terminal_node, websocket=None):
        if websocket:
            await websocket.send_json({
                "type": "simulation_result",
                "reward": reward,
                "terminal_node_id": id(terminal_node),
                "terminal_node_parent_id": id(terminal_node.parent),
                "terminal_node_action": terminal_node.action,
                "terminal_node_description": terminal_node.natural_language_description,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            print(f"Simulation reward: {GREEN}{reward}{RESET}")
            print(f"Simulation terminal node: {GREEN}{terminal_node}{RESET}")
            
    async def websocket_search_complete(self, status, score, path, websocket=None):
        if websocket:
            await websocket.send_json({
                    "type": "search_complete",
                    "status": status,
                    "score": score,
                    "path": path,
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            print(f"Search complete: {GREEN}{status}{RESET}")
            print(f"Search score: {GREEN}{score}{RESET}")
            print(f"Search path: {GREEN}{path}{RESET}")
        
    # shared, not implemented, BFS, DFS and LATS has its own node selection logic
    async def node_selection(self, node, websocket = None):
        NotImplemented
    

    async def node_expansion(self, node: LATSNode, websocket = None) -> None:
        if websocket:
            node_info = {
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description if node.natural_language_description else "Root Node",
                "value": node.value if hasattr(node, 'value') else 0.0,
                "visits": node.visits if hasattr(node, 'visits') else 0,
                "depth": node.depth if hasattr(node, 'depth') else 0,
                "is_terminal": node.is_terminal if hasattr(node, 'is_terminal') else False
            }
            await websocket.send_json({
                "type": "node_expansion_start",
                "node_id": id(node),
                "node_info": node_info,
                "timestamp": datetime.utcnow().isoformat()
            })
        children_state = await self.generate_children(node, websocket)
        children_data = []
        for child_state in children_state:
            child = LATSNode(
                natural_language_description=child_state["natural_language_description"],
                action=child_state["action"],
                prob=child_state["prob"],
                element=child_state["element"],
                goal=node.goal,
                parent=node
            )
            if child.depth == self.config.max_depth:
                child.is_terminal = True
            node.children.append(child)
            children_data.append({
                "id": id(child),
                "parent_id": id(node),
                "action": child.action,
                "description": child.natural_language_description,
                "is_terminal": child.is_terminal,
                "prob": child.prob,
                "depth": child.depth
            })
            await self.websocket_node_created(child, node, websocket=websocket)
        if websocket:
            await websocket.send_json({
                "type": "node_expansion_complete",
                "node_id": id(node),
                "node_info": node_info,
                "children": children_data,
                "timestamp": datetime.utcnow().isoformat()
            })

    
     # node evaluation
     # change the node evaluation to use the new prompt
    async def node_children_evaluation(self, node: LATSNode, websocket=None) -> None:
        if websocket:
            await websocket.send_json({
                "type": "evaluation_start",
                "node_id": id(node),
                "children_count": len(node.children),
                "timestamp": datetime.utcnow().isoformat()
            })
        scores = []
        print(f"{GREEN}-- total {len(node.children)} children to evaluate:{RESET}")
        for i, child in enumerate(node.children):
            print(f"{GREEN}--- evaluating child {i+1}...{RESET}")
            # if child.is_terminal:
            #     score = 0
            # else:
            trajectory = child.get_trajectory()
            if len(trajectory) == 0:
                score = 0
            else:
                prompt = create_llm_prompt(trajectory, self.goal)
                # , child.observation.image
                result = score_trajectory_with_openai(prompt, openai_client, self.config.evaluation_model)
                score = result["overall_score"]
            scores.append(score)
            if websocket:
                await websocket.send_json({
                    "type": "child_evaluated",
                    "node_id": id(child),
                    "parent_id": id(node),
                    "score": score,
                    "timestamp": datetime.utcnow().isoformat()
                })

        for child, score in zip(node.children, scores):
            child.value = score
            # child.reward = score

    async def node_evaluation(self, node: LATSNode, websocket=None) -> None:
        """Evaluate the current node and assign its score."""
        if websocket:
            node_info = {
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description if node.natural_language_description else "Root Node",
                "value": node.value if hasattr(node, 'value') else 0.0,
                "visits": node.visits if hasattr(node, 'visits') else 0,
                "depth": node.depth if hasattr(node, 'depth') else 0,
                "is_terminal": node.is_terminal if hasattr(node, 'is_terminal') else False
            }
            await websocket.send_json({
                "type": "node_evaluation_start",
                "node_id": id(node),
                "node_info": node_info,
                "timestamp": datetime.utcnow().isoformat()
            })
        try:
            # Get the path from root to this node
            path = self.get_path_to_root(node)
            
            # Create trajectory for scoring (skip root node)
            trajectory = []
            for n in path[1:]:  # Skip root node
                trajectory.append({
                    "natural_language_description": n.natural_language_description,
                    "action": n.action,
                    "feedback": n.feedback
                })
            
            try:
                # Score the trajectory
                # if node.is_terminal:
                #     score = 0
                # else:
                if len(trajectory) == 0:
                    score = 0
                else:
                    prompt = create_llm_prompt(trajectory, self.goal)
                    result = score_trajectory_with_openai(
                        prompt, 
                        openai_client, 
                        model=self.config.evaluation_model
                    )
                    score = result["overall_score"]
            
            except Exception as e:
                error_msg = f"Error scoring node {id(node)}: {str(e)}"
                print(error_msg)
                score = float('-inf')
            
            # Assign the score to the node
            node.value = score
            # node.reward = score
            
            if websocket:
                await websocket.send_json({
                    "type": "node_evaluation_complete",
                    "node_id": id(node),
                    "node_info": node_info,
                    "score": score,
                    "trajectory": trajectory,
                    "timestamp": datetime.utcnow().isoformat()
                })

        except Exception as e:
            error_msg = f"Error in node evaluation: {str(e)}"
            print(error_msg)
    
    # shared
    ## TODO: check the logic of updating value/ reward, is the input value?
    def backpropagate(self, node: LATSNode, value: float) -> None:
        while node:
            if node.depth != 0:
                node.visits += 1
                # Calculate running average: newAvg = oldAvg + (value - oldAvg) / newCount
                node.value += (value - node.value) / node.visits
            node = node.parent

    # shared
    async def simulation(self, node: LATSNode, websocket=None) -> tuple[float, LATSNode]:
        depth = node.depth
        num_simulations = self.config.num_simulations
        max_depth = self.config.max_depth
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)
        return await self.rollout(node, websocket=websocket)
    
    # refactor simulation, rollout, send_completion_request methods
    # TODO: check, score as reward and then update value of the starting node?
    async def rollout(self, node: LATSNode, websocket=None)-> tuple[float, LATSNode]:
        # Reset browser state
        live_browser_url, session_id = await self._reset_browser(websocket)
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
        print("current depth: ", len(path) - 1)
        print("max depth: ", self.config.max_depth)

        trajectory, terminal_node = await self.send_completion_request(self.goal, len(path) - 1, node=n, trajectory=trajectory, websocket=websocket)
        print("print the trajectory")
        print_trajectory(terminal_node)
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
        await self.remove_simulated_trajectory(starting_node=node, terminal_node=terminal_node, websocket=websocket)

        return score, terminal_node
    

    # TODO: decide whether to keep the tree update
    async def send_completion_request(self, plan, depth, node, trajectory=[], websocket=None):
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)
        if websocket:
            trajectory_data = self._get_trajectory_data(node)
            await websocket.send_json({
                "type": "trajectory_update",
                "trajectory": trajectory_data,
                "timestamp": datetime.utcnow().isoformat()
            })

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
                ## parent node, new node, for this, the link can be different type, indicating, this is simulated
                ## we don't have node.children.append(child)

                ## new node simulated
                await self.websocket_node_simulated(new_node, node, websocket=websocket)

                if goal_finished:
                    return trajectory, new_node

                return await self.send_completion_request(plan, depth + 1, new_node, trajectory, websocket)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt + 1 == retry_count:
                    print("Max retries reached. Skipping this step and retrying the whole request.")
                    # Retry the entire request from the same state
                    return await self.send_completion_request(plan, depth, node, trajectory, websocket)

        # If all retries and retries of retries fail, return the current trajectory and node
        return trajectory, node



    # # simple search agent generate children method
    # TODO: clean up generate children, no need to put so much information in the websocket
    async def generate_children(self, node: LATSNode, websocket=None) -> list[dict]:
        # Reset browser and get live URL
        live_browser_url, session_id = await self._reset_browser(websocket)
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
                children.append(action)

        if not children:
            node.is_terminal = True        
        return children