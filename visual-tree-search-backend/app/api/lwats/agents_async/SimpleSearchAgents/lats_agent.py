"""Language-based Action Tree Search (LATS) Agent implementation."""

import logging
import time
from typing import Any, Optional, Tuple, List

from openai import OpenAI

from .lats_node import LATSNode, Observation
from ...core_async.config import AgentConfig

from ...webagent_utils_async.action.highlevel import HighLevelActionSet
from ...webagent_utils_async.utils.playwright_manager import AsyncPlaywrightManager, setup_playwright
from .tree_vis import RED, better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
# from ...replay import locate_element_from_action, step_execution
from ...replay_async import generate_feedback, playwright_step_execution, locate_element_from_action
from ...webagent_utils_async.browser_env.observation import extract_page_info, observe_features
from ...webagent_utils_async.action.prompt_functions import generate_actions_with_observation
from ...webagent_utils_async.evaluation.feedback import generate_feedback_with_screenshot
from ...webagent_utils_async.utils.utils import urls_to_images


from ...webagent_utils_async.utils.utils import parse_function_args, locate_element
from ...evaluation_async.evaluators import goal_finished_evaluator
# from ...replay import playwright_step_execution, generate_feedback
from ...webagent_utils_async.action.prompt_functions import extract_top_actions
from ...webagent_utils_async.browser_env.observation import extract_page_info
from .lats_node import LATSNode
from .tree_vis import better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .trajectory_score import create_llm_prompt, score_trajectory_with_openai
from ...webagent_utils_async.action.utils import execute_action
from ...webagent_utils_async.action.prompt_functions import extract_top_actions, is_goal_finished
from ...webagent_utils_async.browser_env.observation import extract_page_info
from ...webagent_utils_async.evaluation.feedback import capture_post_action_feedback

logger = logging.getLogger(__name__)
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

    async def run(self) -> list[LATSNode]:
        """
        Run the LATS search and return the best path found.
        
        Returns:
            list[LATSNode]: Best path from root to terminal node
        """
        pass
        # best_node = self.lats_search()
        # print_trajectory(best_node)
        # return best_node.get_trajectory()

    def lats_search(self) -> LATSNode:
        """
        Perform the main LATS search algorithm.
        
        Returns:
            LATSNode: Best terminal node found
        """        
        logger.info(f"")
        logger.info(f"{GREEN}START SEARCH{RESET}")

        terminal_nodes = []

        for i in range(self.config.iterations):
            logger.info(f"")
            logger.info(f"")
            logger.info(f"Iteration {i + 1}...")
            
            # Step 1: Selection
            logger.info(f"")
            logger.info(f"{GREEN}Step 1: selection{RESET}")
            node = self.select_node(self.root_node)

            if node is None:
                logger.info("All paths lead to terminal nodes with reward 0. Ending search.")
                break

            print(f"{GREEN}Tree:{RESET}")
            better_print(node=self.root_node, selected_node=node)
            print(f"")

            # Step 2: Expansion
            logger.info(f"")
            logger.info(f"{GREEN}Step 2: expansion{RESET}")
            self.expand_node(node)

            while node is not None and node.is_terminal and not self.goal_finished:
                logger.info(f"Depth limit node found at iteration {i + 1}, reselecting...")
                node = self.select_node(self.root_node)
                if node is not None:
                    self.expand_node(node)

            if node is None:
                # all the nodes are terminal, stop the search
                logger.info(f"{RED}All nodes are terminal, stopping search{RESET}")
                break

            if self.goal_finished:
                logger.info(f"{RED}Goal finished, stopping search{RESET}")
                break
            
            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

            # Step 3: Evaluation
            logger.info(f"")
            logger.info(f"{GREEN}Step 3: evaluation{RESET}")
            self.evaluate_node(node)

            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

            # Step 4: Simulation
            logger.info(f"{GREEN}Step 4: simulation{RESET}")
            # # Find the child with the highest value
            ## always = 1
            reward, terminal_node = self.simulate(max(node.children, key=lambda child: child.value), max_depth=self.config.max_depth, num_simulations=1)
            terminal_nodes.append(terminal_node)

            if reward == 1:
                return terminal_node


            # print(f"{GREEN}Tree:{RESET}")
            # better_print(self.root_node, selected_node=terminal_node)
            # print(f"")

            # if self.goal_finished:
            #     logger.info(f"{RED}Goal finished, stopping search{RESET}")
            #     break

            # Step 5: Backpropagation
            logger.info(f"{GREEN}Step 5: backpropagation{RESET}")
            self.backpropagate(terminal_node, reward)
            print(f"{GREEN}Tree:{RESET}")
            better_print(self.root_node)
            print(f"")

        # Find best node
        all_nodes_list = collect_all_nodes(self.root_node)
        all_nodes_list.extend(terminal_nodes)
        
        ## temp change: if reward is the same, choose the deeper node
        best_child = max(all_nodes_list, key=lambda x: (x.reward, x.depth))
        
        if best_child.reward == 1:
            logger.info("Successful trajectory found")
        else:
            logger.info("Unsuccessful trajectory found")
        self.playwright_manager.close()
            
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

    def expand_node(self, node: LATSNode) -> None:
        """
        Expand a node by generating its children.
        
        Args:
            node: Node to expand
        """
        children = self.generate_children(node)

        for child in children:
            node.add_child(child)

        if children and children[0].goal_finish_feedback.is_done:
            self.set_goal_finished(children[0])
            return
        
        node.check_terminal()

    def evaluate_node(self, node: LATSNode) -> None:
        """
        Evaluate a node using LLM scoring.
        
        Args:
            node: Node to evaluate
            
        Returns:
            float: Evaluation score
        """
        scores = []
        logger.info(f"{GREEN}-- total {len(node.children)} children to evaluate:{RESET}")
        for i, child in enumerate(node.children):
            logger.info(f"{GREEN}--- evaluating child {i+1}...{RESET}")
            if child.is_terminal:
                score = 0
            else:
                trajectory = child.get_trajectory()
                prompt = create_llm_prompt(trajectory, self.goal)
                result = score_trajectory_with_openai(prompt, openai_client, self.config.evaluation_model, child.observation.image)
                score = result["score"]/10
            scores.append(score)

        for child, score in zip(node.children, scores):
            child.value = score
            child.reward = score

    def simulate(self, node: LATSNode, max_depth: int = 2, num_simulations=1) -> tuple[float, LATSNode]:
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
        return self.rollout(node, max_depth=max_depth)
    
    def send_completion_request(self, plan, depth, node, trajectory=[]):
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)

        if depth >= self.config.max_depth:
            return trajectory, node

        context = self.playwright_manager.get_context()
        page = self.playwright_manager.get_page()
        # Extract page information
        time.sleep(3)
        page_info = extract_page_info(page, fullpage=True, log_folder=self.config.log_folder)
        updated_actions = extract_top_actions(
            trajectory, self.goal, self.images, page_info, self.action_set, openai_client,
            features=["axtree"], elements_filter="som", branching_factor=self.config.branching_factor,
            log_folder=self.config.log_folder, fullpage=True,
            action_generation_model=self.config.action_generation_model,
            action_grounding_model=self.config.action_grounding_model
        )
        next_action = updated_actions[0]
        retry_count = self.config.retry_count if hasattr(self.config, 'retry_count') else 3  # Default retries if not set
        
        for attempt in range(retry_count):
            try:
                # Convert action to Python code
                code, function_calls = self.action_set.to_python_code(next_action["action"])

                # Locate element
                if len(function_calls) == 1:
                    for function_name, function_args in function_calls:
                        extracted_number = parse_function_args(function_args)
                        element = locate_element(page, extracted_number)
                        next_action["element"] = element
                
                # Execute action
                execute_action(next_action, self.action_set, page, context, self.goal, page_info['interactive_elements'],
                            self.config.log_folder)
                feedback = capture_post_action_feedback(page, next_action, self.goal, self.config.log_folder)
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

                goal_finished = is_goal_finished(messages, openai_client)

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

                return self.send_completion_request(plan, depth + 1, new_node, trajectory)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt + 1 == retry_count:
                    print("Max retries reached. Skipping this step and retrying the whole request.")
                    # Retry the entire request from the same state
                    return self.send_completion_request(plan, depth, node, trajectory)

        # If all retries and retries of retries fail, return the current trajectory and node
        return trajectory, node

    
    def rollout(self, node: LATSNode, max_depth: int = 2)-> tuple[float, LATSNode]:
        # Reset browser state
        self._reset_browser()
        path = self.get_path_to_root(node)
        
        print("execute path")
        # Execute path

        messages = []
        trajectory = []
  
        for n in path[1:]:  # Skip root node
            success = playwright_step_execution(
                n, 
                self.goal, 
                self.playwright_manager, 
                is_replay=False, 
                log_folder=self.config.log_folder
            )
            if not success:
                return 0, n
            if not n.feedback:
                n.feedback = generate_feedback(
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
        trajectory, node = self.send_completion_request(self.goal, len(path) - 1, node=n, trajectory=trajectory)
        print("print the trajectory")
        print_trajectory(node)
        print("print the entire tree")
        print_entire_tree(self.root_node)

        page = self.playwright_manager.get_page()
        page_info = extract_page_info(page, self.config.fullpage, self.config.log_folder)

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

    def _reset_browser(self) -> None:
        """Reset the browser to initial state."""
        self.playwright_manager.close()
        self.playwright_manager = setup_playwright(
            headless=self.config.headless,
            mode=self.config.browser_mode,
            storage_state=self.config.storage_state,
            log_folder=self.config.log_folder,
        )
        page = self.playwright_manager.get_page()
        page.goto(self.starting_url, wait_until="networkidle")

    def observe(self) -> None:
        page = self.playwright_manager.get_page()
        page_info = extract_page_info(page, self.config.fullpage, self.config.log_folder)
        feature_text = observe_features(
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

    def execute_action_trajectory(self, action_trajectory: list[dict]) -> None:
        if not action_trajectory:
            return True

        self._reset_browser()
        for action_data in action_trajectory:
            success = step_execution(action_data, self.playwright_manager, self.config.log_folder)
            if not success:
                return False
        return True

    def generate_candidate_actions(self, node: LATSNode) -> list[dict]:
        trajectory = node.get_trajectory()
        action_trajectory = node.get_action_trajectory()
        self.execute_action_trajectory(action_trajectory)
        observation = self.observe()
        # only root node has no observation at this point
        if node.observation is None:
            node.observation = observation
        actions = generate_actions_with_observation(
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

        page = self.playwright_manager.get_page()
        valid_actions = []
        for action_data in actions:
            if action_data["action"] == "FINISH":
                continue

            is_bid_action, element_data = locate_element_from_action(page, action_data["action"])
            if is_bid_action and not element_data:
                continue

            action_data['element'] = element_data
            valid_actions.append(action_data)
        return valid_actions

    def generate_children(self, node: LATSNode) -> list[LATSNode]:
        logger.info(f"{GREEN}-- generating candidate actions...{RESET}")

        children = []
        
        action_trajectory = node.get_action_trajectory()
        candidate_actions = self.generate_candidate_actions(node)
        logger.info(f"{GREEN}-- generated {len(candidate_actions)} actions{RESET}")
        for action_data in candidate_actions:
            logger.info(f"{GREEN}--- {action_data['action']}{RESET}")
            logger.info(f"{GREEN}--- {action_data['natural_language_description']}{RESET}")

        logger.info(f"")
        logger.info(f"{GREEN}-- executing candidate trajectories{RESET}")
        for i, action_data in enumerate(candidate_actions):

            candidate_action_trajectory = action_trajectory + [action_data]
            logger.info(f"{GREEN}--- trajectory {i+1}:{RESET}")
            for action in candidate_action_trajectory:
                logger.info(f"{GREEN}---- {action['action']}{RESET}")
                logger.info(f"{GREEN}---- {action['natural_language_description']}{RESET}")
            executed_successfully = self.execute_action_trajectory(candidate_action_trajectory)
            if not executed_successfully:
                # not executed successfully, give up this candidate
                logger.info(f"{RED}--- failed to execute action trajectory{RESET}")
                continue

            observation = self.observe()
            logger.info(f"{GREEN}--- generate feedback...{RESET}")
            feedback = generate_feedback_with_screenshot(
                self.goal,
                action_data["natural_language_description"],
                observation.image,
                model=self.config.feedback_model,
            )
            logger.info(f"feedback: is_done: {feedback.is_done}, explanation: {feedback.explanation}")

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
