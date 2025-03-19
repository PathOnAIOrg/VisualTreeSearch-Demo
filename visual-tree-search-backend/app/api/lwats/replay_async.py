import sys
import os
import base64

from .webagent_utils_async.action.action_parser import parse_action

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .webagent_utils_async.browser_env.observation import (
    _pre_extract,
    _post_extract,
    extract_dom_snapshot,
    extract_dom_extra_properties,
    extract_merged_axtree,
    extract_focused_element_bid,
)
from .webagent_utils_async.browser_env.extract_elements import extract_interactive_elements
from openai import OpenAI
import os
import re
import json
from .webagent_utils_async.utils.utils import encode_image, locate_element
from dotenv import load_dotenv
_ = load_dotenv()
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Initialize the Eleven Labs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import argparse
from .webagent_utils_async.action.highlevel import HighLevelActionSet
from .webagent_utils_async.utils.playwright_manager import AsyncPlaywrightManager
from .webagent_utils_async.action.base import execute_python_code_safely
import time
import logging
from .webagent_utils_async.browser_env.obs import flatten_axtree_to_str, flatten_dom_to_str

logger = logging.getLogger(__name__)
from .webagent_utils_async.utils.utils import setup_logger
import os
import time
import re
import logging


def read_steps_json(file_path):
    goal = None
    starting_url = None
    steps = []

    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return goal, starting_url, steps

    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            if i == 0:
                # First line is the starting_url (plain string)
                goal = line.strip()
            if i == 1:
                # First line is the starting_url (plain string)
                starting_url = line.strip()
            else:
                try:
                    # Subsequent lines are JSON objects
                    step = json.loads(line.strip())
                    steps.append(step)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON on line {i + 1}: {line}")
                    print(f"Error message: {str(e)}")

    return goal, starting_url, steps



# Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=) search running shoes, click on the first result <lwats.webagent_utils_async.utils.playwright_manager.AsyncPlaywrightManager object at 0x126dcd110> False log
# page: <Page url='http://128.105.145.205:7770/'>
# node: Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=)
# node.element: <coroutine object locate_element at 0x10db66880>
# Error in locate_element: Connection closed
# selector: body
# element: <Locator frame=<Frame name= url='http://128.105.145.205:7770/'> selector='body'>
# {}
# element count before: 1
# element count after: 1
# ERROR:lwats.replay_async:Error occurred during execution: Error: Element is not an <input>, <textarea> or [contenteditable] element




# Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=) search running shoes, click on the first result <lwats.webagent_utils_async.utils.playwright_manager.AsyncPlaywrightManager object at 0x1244aee10> False log
# page: <Page url='http://128.105.145.205:7770/'>
# node: Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=)
# node.element: {'text': '', 'type': 'text', 'tag': 'input', 'id': 'search', 'name': 'q', 'value': '', 'placeholder': 'Search entire store here...', 'class': 'input-text', 'role': 'combobox'}
# selector: body
# element: <Locator frame=<Frame name= url='http://128.105.145.205:7770/'> selector='body'>
# {'text': '', 'type': 'text', 'tag': 'input', 'id': 'search', 'name': 'q', 'value': '', 'placeholder': 'Search entire store here...', 'class': 'input-text', 'role': 'combobox'}
# element count before: 1
# element count after: 1
# ERROR:lwats.replay_async:Error occurred during execution: Error: Element is not an <input>, <textarea> or [contenteditable] element


# Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=) search running shoes, click on the first result <lwats.webagent_utils_sync.utils.playwright_manager.PlaywrightManager object at 0x111584210> False log
# page: <Page url='http://128.105.145.205:7770/'>
# node: Node(depth=1, value=0.00, visits=0, action=fill('274', 'running shoes'), feedback=)
# selector: #search
# element: <Locator frame=<Frame name= url='http://128.105.145.205:7770/'> selector='#search'>
# {'text': '', 'type': 'text', 'tag': 'input', 'id': 'search', 'name': 'q', 'value': '', 'placeholder': 'Search entire store here...', 'class': 'input-text', 'role': 'combobox', 'unique_selector': '#search', 'selector_uniqueness_validated': True}
# element count before: 1
# element count after: 1


async def playwright_step_execution(node, goal, playwright_manager, is_replay, log_folder):
    logger = logging.getLogger(__name__)
    context = await playwright_manager.get_context()
    page = await playwright_manager.get_page()
    url = page.url
    print(node, goal, playwright_manager, is_replay, log_folder)
    print(f"page: {page}")
    print(f"node: {node}")
    print(f"node.element: {node.element}")
    # If node.element is a coroutine, await it
    if hasattr(node.element, '__await__'):
        step_data = await node.element
    else:
        step_data = node.element
        
    selector = step_data.get("unique_selector", "body")
    element = page.locator(selector)
    print(f"selector: {selector}")
    print(f"element: {element}")
    print(step_data)

    logger.info(f"==> Attempting action with selector: {selector}")
    logger.info(f"Node data: {node}")
    logger.info(f"Current page URL: {url}")

    action = node.action

    # Await the count() method
    print(f"element count before: {await element.count()}")

    #
    # 1) Wait until attached & visible
    #
    try:
        logger.info(f"Waiting for element to be attached: {selector}")
        await element.wait_for(state="attached", timeout=10_000)
        logger.info(f"Waiting for element to be visible: {selector}")
        await element.wait_for(state="visible", timeout=10_000)
    except Exception as e:
        logger.error(f"Error while waiting for element to become visible: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_wait.png')
        await page.screenshot(path=debug_screenshot_path)
        logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
        return False
    
    # Await the count() method
    print(f"element count after: {await element.count()}")

    #
    # 2) Execute action
    #
    try:
        action_name, args, kwargs = parse_action(action)
        await execute_action(page, element, action_name, args, kwargs)
        return True
    except Exception as e:
        logger.error(f"Error occurred during execution: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_action.png')
        await page.screenshot(path=debug_screenshot_path)
        logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
        return False

BID_ACTIONS = [
    "fill",
    "check",
    "uncheck",
    "select_option",
    "click",
    "dblclick",
    "hover",
    "press",
    "focus",
    "clear",
    # "drag_and_drop",
    "upload_file",
]



async def locate_element_from_action(page, action):
    action_name, args, kwargs = parse_action(action)
    is_bid_action = action_name in BID_ACTIONS
    print(f"action: {action}")
    print(f"action_name: {action_name}")
    if is_bid_action:
        element_data = await locate_element(page, args[0])
    else:
        element_data = None
    print(f"element_data: {element_data}")
    return is_bid_action, element_data

async def step_execution(action_data, playwright_manager, log_folder):
    logger = logging.getLogger(__name__)
    page = await playwright_manager.get_page()
    url = page.url

    action = action_data["action"]
    action_name, args, kwargs = parse_action(action)

    if action_data['element'] is not None:
        selector = action_data['element'].get("unique_selector", "body")
        element = await page.locator(selector)
    else:
        selector = "no element"
        element = None

    logger.info(f"==> Exectute Action: {action}")
    logger.info(f"Current page URL: {url}")
    logger.info(f"Selector: {selector}")

    #
    # 1) Wait until attached & visible
    #
    if element is not None:
        try:
            logger.info(f"Waiting for element to be attached: {selector}")
            await element.wait_for(state="attached", timeout=10_000)
            logger.info(f"Waiting for element to be visible: {selector}")
            await element.wait_for(state="visible", timeout=10_000)
        except Exception as e:
            logger.error(f"Error while waiting for element to become visible: {e}")
            debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_wait.png')
            await page.screenshot(path=debug_screenshot_path)
            logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
            return False
    
    #
    # 2) Execute action
    #
    try:
        await execute_action(page, element, action_name, args, kwargs)
        return True
    except Exception as e:
        logger.error(f"Error occurred during execution: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_action.png')
        await page.screenshot(path=debug_screenshot_path)
        logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
        return False


async def execute_action(page, element, action_name, args, kwargs):
    # TODO: add timeout
    match action_name:
        case "noop":
            await page.wait_for_timeout(args[0])
        case "fill":
            await element.fill(args[1])
        case "check":
            await element.check()
        case "uncheck":
            await element.uncheck()
        case "select_option":
            await element.select_option(args[1])
        case "click":
            await element.click(**kwargs)
        case "dblclick":
            await element.dblclick(**kwargs)
        case "hover":
            await element.hover()
        case "press":
            await element.press(args[1])
        case "focus":
            await element.focus()
        case "clear":
            await element.clear()
        # case "drag_and_drop":
        #     drag_and_drop(args[0], args[1])
        case "scroll":
            await page.mouse.wheel(args[0], args[1])
        case "mouse_move":
            await page.mouse.move(args[0], args[1])
        case "mouse_up":
            await page.mouse.up(args[0], args[1], **kwargs)
        case "mouse_down":
            await page.mouse.down(args[0], args[1], **kwargs)
        case "mouse_click":
            await page.mouse.click(args[0], args[1], **kwargs)
        case "mouse_dblclick":
            await page.mouse.dblclick(args[0], args[1], **kwargs)
        case "mouse_drag_and_drop":
            await page.mouse.move(args[0], args[1])
            await page.mouse.down()
            await page.mouse.move(args[2], args[3])
            await page.mouse.up()
        case "keyboard_press":
            await page.keyboard.press(args[0])
        case "keyboard_up":
            await page.keyboard.up(args[0])
        case "keyboard_down":
            await page.keyboard.down(args[0])
        case "keyboard_type":
            await page.keyboard.type(args[0])
        case "keyboard_insert_text":
            await page.keyboard.insert_text(args[0])
        case "goto":
            await page.goto(args[0])
        case "go_back":
            await page.go_back()
        case "go_forward":
            await page.go_forward()
        case "new_tab":
            page = await page.context.new_page()
            # trigger the callback that sets this page as active in browsergym
            await page.locate("html").dispatch_event("pageshow")
        case "tab_close":
            context = page.context
            await page.close()
            if context.pages:
                page = context.pages[-1]
            else:
                page = context.new_page()
            await page.locate("html").dispatch_event("pageshow")
        case "tab_focus":
            page = page.context.pages[args[0]]
            await page.locate("html").dispatch_event("pageshow")
        case "upload_file":
            with page.expect_file_chooser() as fc_info:
                await element.click()

            file_chooser = fc_info.value
            file_chooser.set_files(args[1])
        case "mouse_upload_file":
            with page.expect_file_chooser() as fc_info:
                await page.mouse.click(args[0], args[1])

            file_chooser = fc_info.value
            file_chooser.set_files(args[2])
        case _:
            raise ValueError(f"Unknown action: {action_name}")



async def generate_feedback(goal, action_description, playwright_manager, model="gpt-4o"):
    page = await playwright_manager.get_page()

    await page.wait_for_timeout(3000)

    screenshot_bytes = await page.screenshot()
    base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')

    system_prompt = f"""
    You are a helpful assitant. Given a goal, a screenshot of the current web page and a description of the action taken, provide a natural language description of current page state related to the goal.
    """

    # Build and send prompt to OpenAI
    prompt = f"""
    # Goal:
    {goal}

    # Action description:
    {action_description}

    Please provide a natural language description of current page state. It must be related to the goal.
    """
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ],
            },
        ],
    )

    feedback = response.choices[0].message.content
    logger.info(f"Feedback from OpenAI: {feedback}")

    return feedback

if __name__ == "__main__":
    import asyncio
    
    async def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
        parser.add_argument('--steps_file', type=str, default=None, help='Path to the steps JSON file')
        parser.add_argument('--url', type=str, default=None, help='Starting URL if not using steps file')
        args = parser.parse_args()

        log_folder = args.log_folder
        logger = setup_logger()
        
        # Create necessary directories
        os.makedirs(os.path.join(log_folder, 'screenshots'), exist_ok=True)
        
        # Initialize AsyncPlaywrightManager
        playwright_manager = AsyncPlaywrightManager(storage_state=None)
        browser = await playwright_manager.get_browser()
        context = await playwright_manager.get_context()
        page = await playwright_manager.get_page()
        playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
        
        # Set viewport size
        await page.set_viewport_size({"width": 1440, "height": 900})
        
        if args.steps_file:
            # Read steps from file
            goal, starting_url, steps = read_steps_json(args.steps_file)
            await page.goto(starting_url)
            
            print(f"Goal: {goal}")
            print(f"Starting URL: {starting_url}")
            print(f"Found {len(steps)} steps to execute")
            
            for i, step in enumerate(steps, 1):
                print(f"\nExecuting Step {i}/{len(steps)}:")
                print(json.dumps(step, indent=2))
                
                # Create a simple node-like structure for the step
                class Node:
                    def __init__(self, element, action):
                        self.element = element
                        self.action = action
                    
                    def __str__(self):
                        return f"Node(action={self.action}, element={self.element})"
                
                node = Node(step.get('element', {}), step.get('action', ''))
                
                # Execute the step
                success = await playwright_step_execution(node, goal, playwright_manager, True, log_folder)
                
                if success:
                    print(f"Step {i} executed successfully")
                    # Generate feedback about the current state
                    feedback = await generate_feedback(goal, step.get('action', ''), playwright_manager)
                    print(f"Feedback: {feedback}")
                else:
                    print(f"Step {i} failed")
                    break
                
                # Wait a bit between steps
                await asyncio.sleep(2)
        else:
            # Simple manual test if no steps file provided
            if args.url:
                await page.goto(args.url)
            else:
                await page.goto("http://128.105.145.205:7770/")  # Default URL from your debug output
            
            print("Manual test mode - executing a single fill action")
            
            # Create a test node with a fill action
            class Node:
                def __init__(self, element, action):
                    self.element = element
                    self.action = action
                
                def __str__(self):
                    return f"Node(action={self.action}, element={self.element})"
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Create a test element and action
            test_element = {"unique_selector": "#search"}
            test_action = "fill('274', 'running shoes')"
            
            node = Node(test_element, test_action)
            
            # Execute the action
            goal = "Search for running shoes"
            success = await playwright_step_execution(node, goal, playwright_manager, True, log_folder)
            
            if success:
                print("Test action executed successfully")
                # Generate feedback
                feedback = await generate_feedback(goal, test_action, playwright_manager)
                print(f"Feedback: {feedback}")
            else:
                print("Test action failed")
        
        # Take a final screenshot
        final_screenshot_path = os.path.join(log_folder, 'screenshots', 'final_state.png')
        await page.screenshot(path=final_screenshot_path)
        print(f"Final screenshot saved to: {final_screenshot_path}")
        
        # Clean up
        await playwright_manager.close()
        print("Test completed")

    # Run the async main function
    asyncio.run(main())

