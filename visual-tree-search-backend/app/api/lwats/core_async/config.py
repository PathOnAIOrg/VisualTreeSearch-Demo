from dataclasses import dataclass, field, fields
from typing import List, Optional

@dataclass
class AgentConfig:
    # Browser settings
    headless: bool = False
    browser_mode: str = "browserbase"
    storage_state: str = 'state.json'
    
    # Model settings
    default_model: str = "gpt-4o-mini"
    action_generation_model: str = "gpt-4o-mini"
    feedback_model: str = "gpt-4o-mini"
    planning_model: str = "gpt-4o"
    action_grounding_model: str = "gpt-4o"
    evaluation_model: str = "gpt-4o"
    # Search settings
    search_algorithm: str = "bfs"
    exploration_weight: float = 1.41
    branching_factor: int = 5
    iterations: int = 1
    max_depth: int = 3
    num_simulations: int = 100
    
    # Features
    features: List[str] = field(default_factory=lambda: ['axtree'])
    fullpage: bool = False
    elements_filter: str = "som"

    # Logging
    log_folder: str = "log"

def add_agent_config_arguments(parser):
    # Environment
    parser.add_argument("--browser-mode", type=str, required=False,
                        help="Specify the browser mode")
    parser.add_argument("--storage-state", type=str, required=False,
                        help="Storage state json file")
    # Model
    parser.add_argument("--action_generation_model", type=str, required=False,
                        help="action generation model, right now only supports openai models")
    parser.add_argument("--feedback_model", type=str, required=False,
                        help="feedback model, right now only supports openai models")
    parser.add_argument("--planning_model", type=str, required=False,
                        help="planning model, right now only supports openai models")
    parser.add_argument("--action_grounding_model", type=str, required=False,
                        help="action grounding model, right now only supports openai models")
    parser.add_argument("--evaluation_model", type=str, required=False,
                        help="evaluation model, right now only supports openai models")
    # Search
    parser.add_argument("--search_algorithm", type=str, required=False,
                        help="bfs or dfs")
    parser.add_argument("--exploration_weight", type=float, required=False,
                        help="exploration weight")
    parser.add_argument("--branching_factor", type=int, required=False,
                        help="branching factor")
    parser.add_argument("--iterations", type=int, required=False,
                        help="Number of iterations to run")
    parser.add_argument("--max_depth", type=int, required=False,
                        help="max depth of rollout")
    parser.add_argument("--num_simulations", type=int, required=False,
                        help="Number of simulations to run")
    
    # Features
    parser.add_argument("--features", type=str, required=False,
                        help="features to use")
    parser.add_argument("--fullpage", type=bool, required=False,
                        help="fullpage")
    parser.add_argument("--elements_filter", type=str, required=False,
                        help="elements filter")

    # Logging
    parser.add_argument("--log_folder", type=str, required=False,
                        help="log folder")
    
def filter_valid_config_args(args_dict):
    valid_fields = {field.name for field in fields(AgentConfig)}
    return {k: v for k, v in args_dict.items() if k in valid_fields and v is not None}