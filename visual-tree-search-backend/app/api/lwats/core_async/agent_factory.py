import sys
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

from .config import AgentConfig
from ..agents_async.SimpleSearchAgents.simple_search_agent import SimpleSearchAgent
from ..webagent_utils_async.utils.utils import setup_logger
from ..webagent_utils_async.utils.playwright_manager import setup_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ = load_dotenv()

logger = logging.getLogger(__name__)
openai_client = OpenAI()

# Define the default features
DEFAULT_FEATURES = ['screenshot', 'dom', 'axtree', 'focused_element', 'extra_properties', 'interactive_elements']


SEARCH_AGENT_SYSTEM_PROMPT = \
"""You are a web search agent designed to perform specific tasks on web pages as instructed by the user. Your primary objectives are:

1. Execute ONLY the task explicitly provided by the user.
2. Perform the task efficiently and accurately using the available functions.
3. If there are errors, retry using a different approach within the scope of the given task.
4. Once the current task is completed, stop and wait for further instructions.

Critical guidelines:
- Strictly limit your actions to the current task. Do not attempt additional tasks or next steps.
- Use only the functions provided to you. Do not attempt to use functions or methods that are not explicitly available.
- For navigation or interaction with page elements, always use the appropriate bid (browser element ID) when required by a function.
- Do not try to navigate to external websites or use URLs directly.
- If a task cannot be completed with the available functions, report the limitation rather than attempting unsupported actions.
- After completing a task, report its completion and await new instructions. Do not suggest or initiate further actions.

Remember: Your role is to execute the given task precisely as instructed, using only the provided functions and within the confines of the current web page. Do not exceed these boundaries under any circumstances."""

async def setup_search_agent(
    agent_type,
    starting_url,
    goal,
    images,
    agent_config: AgentConfig
):
    logger = setup_logger()

    file_path = os.path.join(agent_config.log_folder, 'flow', 'steps.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        file.write(goal + '\n')
        file.write(starting_url + '\n')

    playwright_manager = await setup_playwright(
        headless=agent_config.headless, 
        mode=agent_config.browser_mode,
        storage_state=agent_config.storage_state
    )
    # storage_state='state.json', headless=False, mode="chromium"

    page = await playwright_manager.get_page()
    await page.goto(starting_url)
    # Maximize the window on macOS
    # await page.set_viewport_size({"width": 1440, "height": 900})

    messages = [{
        "role": "system",
        "content": SEARCH_AGENT_SYSTEM_PROMPT,
    }]

    if agent_type == "SimpleSearchAgent":
        agent = SimpleSearchAgent(
            starting_url=starting_url,
            messages=messages,
            goal=goal,
            images = images,
            playwright_manager=playwright_manager,
            config=agent_config,
        )
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'FunctionCallingAgent', 'HighLevelPlanningAgent', 'ContextAwarePlanningAgent', 'PromptAgent' or 'PromptSearchAgent' ."
        logger.error(error_message)
        return {"error": error_message}
    return agent, playwright_manager