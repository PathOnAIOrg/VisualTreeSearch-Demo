import sys
import os
import base64

from .webagent_utils_sync.action.action_parser import parse_action

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .webagent_utils_sync.browser_env.observation import (
    _pre_extract,
    _post_extract,
    extract_dom_snapshot,
    extract_dom_extra_properties,
    extract_merged_axtree,
    extract_focused_element_bid,
)
from .webagent_utils_sync.browser_env.extract_elements import extract_interactive_elements
from openai import OpenAI
import os
import re
import json
from .webagent_utils_sync.utils.utils import encode_image, locate_element
from dotenv import load_dotenv
_ = load_dotenv()
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Initialize the Eleven Labs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import argparse
from .webagent_utils_sync.action.highlevel import HighLevelActionSet
from .webagent_utils_sync.utils.playwright_manager import PlaywrightManager
from .webagent_utils_sync.action.base import execute_python_code_safely
import time
import logging
from .webagent_utils_sync.browser_env.obs import flatten_axtree_to_str, flatten_dom_to_str

logger = logging.getLogger(__name__)
from .webagent_utils_sync.utils.utils import setup_logger
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


# def find_matching_element(interactive_elements, target):
#     for element in interactive_elements:
#         if (element.get('text', '').lower() == target.get('text', '').lower() and
#                 element.get('tag') == target.get('tag') and
#                 target.get('id') == element.get('id')):
#             return element
#     return None


# def find_match(interactive_elements, key, value):
#     for element in interactive_elements:
#         if element.get(key, '') == value:
#             return element
#     return None


# def replace_number(text, new_number):
#     # Find the first number in the string and replace it
#     return re.sub(r'\d+', str(new_number), text)


def playwright_step_execution(node, goal, playwright_manager, is_replay, log_folder):
    logger = logging.getLogger(__name__)
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    url = page.url

    step_data = node.element
    selector = step_data.get("unique_selector", "body")
    element = page.locator(selector)

    logger.info(f"==> Attempting action with selector: {selector}")
    logger.info(f"Node data: {node}")
    logger.info(f"Current page URL: {url}")

    action = node.action

    print(f"element count before: {element.count()}")

    #
    # 1) Wait until attached & visible
    #
    try:
        logger.info(f"Waiting for element to be attached: {selector}")
        element.wait_for(state="attached", timeout=10_000)
        logger.info(f"Waiting for element to be visible: {selector}")
        element.wait_for(state="visible", timeout=10_000)
    except Exception as e:
        logger.error(f"Error while waiting for element to become visible: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_wait.png')
        page.screenshot(path=debug_screenshot_path)
        logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
        return False
    
    print(f"element count after: {element.count()}")

    #
    # 2) Execute action
    #
    try:
        action_name, args, kwargs = parse_action(action)
        execute_action(page, element, action_name, args, kwargs)
        return True
    except Exception as e:
        logger.error(f"Error occurred during execution: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_action.png')
        page.screenshot(path=debug_screenshot_path)
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



def locate_element_from_action(page, action):
    action_name, args, kwargs = parse_action(action)
    is_bid_action = action_name in BID_ACTIONS
    if is_bid_action:
        element_data = locate_element(page, args[0])
    else:
        element_data = None
    return is_bid_action, element_data

def step_execution(action_data, playwright_manager, log_folder):
    logger = logging.getLogger(__name__)
    page = playwright_manager.get_page()
    url = page.url

    action = action_data["action"]
    action_name, args, kwargs = parse_action(action)

    if action_data['element'] is not None:
        selector = action_data['element'].get("unique_selector", "body")
        element = page.locator(selector)
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
            element.wait_for(state="attached", timeout=10_000)
            logger.info(f"Waiting for element to be visible: {selector}")
            element.wait_for(state="visible", timeout=10_000)
        except Exception as e:
            logger.error(f"Error while waiting for element to become visible: {e}")
            debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_wait.png')
            page.screenshot(path=debug_screenshot_path)
            logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
            return False
    
    #
    # 2) Execute action
    #
    try:
        execute_action(page, element, action_name, args, kwargs)
        return True
    except Exception as e:
        logger.error(f"Error occurred during execution: {e}")
        debug_screenshot_path = os.path.join(log_folder, 'screenshots', 'error_action.png')
        page.screenshot(path=debug_screenshot_path)
        logger.error(f"Saved debug screenshot: {debug_screenshot_path}")
        return False


def execute_action(page, element, action_name, args, kwargs):
    # TODO: add timeout
    match action_name:
        case "noop":
            page.wait_for_timeout(args[0])
        case "fill":
            element.fill(args[1])
        case "check":
            element.check()
        case "uncheck":
            element.uncheck()
        case "select_option":
            element.select_option(args[1])
        case "click":
            element.click(**kwargs)
        case "dblclick":
            element.dblclick(**kwargs)
        case "hover":
            element.hover()
        case "press":
            element.press(args[1])
        case "focus":
            element.focus()
        case "clear":
            element.clear()
        # case "drag_and_drop":
        #     drag_and_drop(args[0], args[1])
        case "scroll":
            page.mouse.wheel(args[0], args[1])
        case "mouse_move":
            page.mouse.move(args[0], args[1])
        case "mouse_up":
            page.mouse.up(args[0], args[1], **kwargs)
        case "mouse_down":
            page.mouse.down(args[0], args[1], **kwargs)
        case "mouse_click":
            page.mouse.click(args[0], args[1], **kwargs)
        case "mouse_dblclick":
            page.mouse.dblclick(args[0], args[1], **kwargs)
        case "mouse_drag_and_drop":
            page.mouse.move(args[0], args[1])
            page.mouse.down()
            page.mouse.move(args[2], args[3])
            page.mouse.up()
        case "keyboard_press":
            page.keyboard.press(args[0])
        case "keyboard_up":
            page.keyboard.up(args[0])
        case "keyboard_down":
            page.keyboard.down(args[0])
        case "keyboard_type":
            page.keyboard.type(args[0])
        case "keyboard_insert_text":
            page.keyboard.insert_text(args[0])
        case "goto":
            page.goto(args[0])
        case "go_back":
            page.go_back()
        case "go_forward":
            page.go_forward()
        case "new_tab":
            page = page.context.new_page()
            # trigger the callback that sets this page as active in browsergym
            page.locate("html").dispatch_event("pageshow")
        case "tab_close":
            context = page.context
            page.close()
            if context.pages:
                page = context.pages[-1]
            else:
                page = context.new_page()
            page.locate("html").dispatch_event("pageshow")
        case "tab_focus":
            page = page.context.pages[args[0]]
            page.locate("html").dispatch_event("pageshow")
        case "upload_file":
            with page.expect_file_chooser() as fc_info:
                element.click()

            file_chooser = fc_info.value
            file_chooser.set_files(args[1])
        case "mouse_upload_file":
            with page.expect_file_chooser() as fc_info:
                page.mouse.click(args[0], args[1])

            file_chooser = fc_info.value
            file_chooser.set_files(args[2])
        case _:
            raise ValueError(f"Unknown action: {action_name}")



def generate_feedback(goal, action_description, playwright_manager, model="gpt-4o"):
    page = playwright_manager.get_page()

    page.wait_for_timeout(3000)

    screenshot_bytes = page.screenshot()
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


# def browsergym_step_execution(step, goal, playwright_manager, is_replay, log_folder):
#     time.sleep(5)
#     context = playwright_manager.get_context()
#     page = playwright_manager.get_page()
#     action_set = HighLevelActionSet(
#         subsets=["bid", "nav"],
#         strict=False,
#         multiaction=True,
#         demo_mode="off"
#     )

#     _pre_extract(page)
#     dom = extract_dom_snapshot(page)
#     axtree = extract_merged_axtree(page)
#     focused_element_bid = extract_focused_element_bid(page)
#     extra_properties = extract_dom_extra_properties(dom)
#     interactive_elements = extract_interactive_elements(page)
#     _post_extract(page)
#     url = page.url
#     try:
#         import pdb; pdb.set_trace()
#         if step['element'] != None:
#             # debug finding matching element
#             element = find_matching_element(interactive_elements, step['element'])
#             if element:
#                 action = replace_number(step["action"], element['bid'])
#             else:
#                 action = step["action"]
#         else:
#             action = step["action"]
#     except:
#         print(step)
#         import pdb; pdb.set_trace()
#     code, function_calls = action_set.to_python_code(action)
#     logger.info("Executing action script")
#     # Execute code in the main thread
#     code_file_path = execute_python_code_safely(
#             code,
#             page,
#             context,
#             log_folder,
#             send_message_to_user=None,
#             report_infeasible_instructions=None
#     )

#     # if is_replay:
#     task_description = goal
#     page = playwright_manager.get_page()
#     # screenshot_path_post = os.path.join(log_folder, 'screenshots', 'screenshot_post.png')
#     time.sleep(3)
#     # page.screenshot(path=screenshot_path_post)
#     # base64_image = encode_image(screenshot_path_post)

#     screenshot_bytes = page.screenshot()
#     # Encode the bytes to base64
#     base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
#     prompt = f"""
#                 After we take action {action}, a screenshot was captured.

#                 # Screenshot description:
#                 The image provided is a screenshot of the application state after the action was performed.

#                 # The original goal:
#                 {task_description}

#                 Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
#                 """

#     # Query OpenAI model
#     response = openai_client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt},
#                     {"type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/jpeg;base64,{base64_image}",
#                         "detail": "high"
#                     }
#                     }
#                 ]
#                 },
#         ],
#     )

#     feedback = response.choices[0].message.content
#     return feedback


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    args = parser.parse_args()

    log_folder = args.log_folder
    logger = setup_logger(log_folder, log_file="replay_log.txt")
    # Example usage
    playwright_manager = PlaywrightManager(storage_state=None, video_dir=os.path.join(args.log_folder, 'videos'))
    browser = playwright_manager.get_browser()
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    file_path = os.path.join(log_folder, 'flow', 'steps.json')
    goal, starting_url, steps = read_steps_json(file_path)
    page.goto(starting_url)
    page.set_viewport_size({"width": 1440, "height": 900})
    messages = [{"role": "system",
                 "content": "You are a smart web search agent to perform search and click task, upload files for customers"}]
    for i, step in enumerate(steps, 1):
        print(f"Step {i}:")
        print(json.dumps(step))
        task_description = step["task_description"]
        action, feedback = take_action(step, playwright_manager, True, log_folder)
        content = "The task_description is: {}, the action is: {} and the feedback is: {}".format(task_description,
                                                                                                  action, feedback)
        messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": "summarize the status of the task, be concise"})
    response = openai_client.chat.completions.create(model="gpt-4o", messages=messages)
    summary = response.choices[0].message.content
    playwright_manager.close()
    print(summary)
    audio = elevenlabs_client.generate(
        text=summary,
        voice="Rachel",
        model="eleven_multilingual_v2"
    )
    play(audio)
