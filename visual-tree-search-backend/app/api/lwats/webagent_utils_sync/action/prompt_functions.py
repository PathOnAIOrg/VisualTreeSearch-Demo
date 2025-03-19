from datetime import datetime
import json
import os

from litellm import OpenAI
from ..utils.utils import url_to_b64
from .utils import prepare_prompt
from .utils import build_highlevel_action_parser
from collections import defaultdict
from PIL import Image
import base64
from io import BytesIO
import requests

def is_goal_finished(messages, openai_client: OpenAI):
    from pydantic import BaseModel
    class Plan(BaseModel):
        goal_finished: bool

    new_response = openai_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=Plan,
    )
    message = new_response.choices[0].message.parsed

    goal_finished = message.goal_finished
    return goal_finished

# TODO: make this consistent with https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/agents/PromptAgents/PromptAgent.py
def extract_top_actions(trajectory, goal, images, page_info, action_set, openai_client: OpenAI,
                        features, elements_filter, branching_factor, log_folder, fullpage=True, action_generation_model="gpt-4o", action_grounding_model="gpt-4o"):
    if len(images) == 0:
        print("the input is just text")
        system_msg = f"""
            # Instructions
            Review the current state of the page and all other information to find the best
            possible next action and a natural language description of the action (example of natural language description is like)
            "click the navbar button" or "select the portrait option" etc) to accomplish your goal.
            Your answer will be interpreted and executed by a program, make sure to follow the formatting instructions.
            
            Respond using valid JSON format, which can be parsed by python json.loads(), with keys:
            - context (containing the action)
            - natural_language_description
            - finished (boolean: IMPORTANT - must be False if content field contains an action.
                    Only set to True when NO more actions are needed and content field is empty)
            
            Example response format:
            {{
                "content": "action here",
                "natural_language_description": "description here",
                "finished": false  # Must be false because content contains an action
            }}
            
            # Rules for finished field:
            - If content field contains any action: finished MUST be False
            - Only set finished to True when:
                1. The goal is completely achieved
                2. No more actions are needed
                3. Content field is empty
            
            Previous actions and action results are: {trajectory}
            
            Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
            
            # Goal:
            {goal}
            """
        messages = [{"role": "system", "content": system_msg}]
    else:
        print("using images as well")
        system_msg = f"""
            # Instructions
            Review the current state of the page and all other information to find the best
            possible next action and a natural language description of the action (example of natural language description is like)
            "click the navbar button" or "select the portrait option" etc) to accomplish your goal.
            Your answer will be interpreted and executed by a program, make sure to follow the formatting instructions.
            
            Respond using JSON format, with keys:
            - context (containing the action)
            - natural_language_description
            - finished (boolean: IMPORTANT - must be False if content field contains an action.
                    Only set to True when NO more actions are needed and content field is empty)
            
            Example response format:
            {{
                "content": "action here",
                "natural_language_description": "description here",
                "finished": false  # Must be false because content contains an action
            }}
            
            # Rules for finished field:
            - If content field contains any action: finished MUST be False
            - Only set finished to True when:
                1. The goal is completely achieved
                2. No more actions are needed
                3. Content field is empty
            
            Previous actions and action results are: {trajectory}
            
            Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
            
            # Goal:
            {goal}, and here are the input images
            """
        messages = [{"role": "system", "content": system_msg}]
        content = []
        for image_i, image in enumerate(images):
            content.extend(
                [
                    {
                        "type": "text",
                        "text": f"({image_i+2}) input image {image_i+1}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": url_to_b64(image)},
                    },
                ]
            )
        messages.append({"role": "user", "content": content})

    prompt = prepare_prompt(page_info, action_set, features, elements_filter, log_folder, fullpage)
    # base64_image = encode_image(page_info['screenshot'])
    base64_image = base64.b64encode(page_info['screenshot_som']).decode('utf-8')
    print("action generation model is: {}".format(action_generation_model))
    messages.append({"role": "user",
             "content": [
                 {"type": "text", "text": prompt},
                 {"type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}",
                      "detail": "high"
                  }
                  }
             ]
             })

    response = openai_client.chat.completions.create(
        model=action_generation_model,
        response_format= {"type": "json_object"},  # Enable JSON mode
        messages=messages,
        logprobs=True,
        n=min(branching_factor * 2, 20),
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"action_gen_sys_prompt_{timestamp}.txt"
    file_path = os.path.join(log_folder, 'prompt', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf8') as file:
        file.write(system_msg)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"action_gen_res_{timestamp}.json"
    file_path = os.path.join(log_folder, 'prompt', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf8') as file:
        file.write(response.model_dump_json())
    # check whether the task is finished, based on is finished
    # action, description, is_finished

    # responses: list[str] = [x.message.content for x in response.choices]
    import json
    import math
    #responses: list[dict] = [json.loads(x.message.content) for x in response.choices]
    #probs = [math.exp(x.logprobs.content[0].logprob) for x in response.choices]

    # Parse responses and probabilities, skipping invalid JSON entries
    responses = []
    probs = []

    def is_valid_json(string):
        try:
            result = json.loads(string)
            if "content" in result and "natural_language_description" in result and "finished" in result:
                return True
            else:
                print("can be loaded into dictionary, but doesn't have all the required fields")
                return False
        except:
            print("cannot be loaded into dictionary")
            return False

    # add error handling
    for i, choice in enumerate(response.choices):
        if is_valid_json(choice.message.content):
            # Attempt to parse the response content as JSON
            parsed_response = json.loads(choice.message.content)
            # If successful, add the parsed response and associated probability
            responses.append(parsed_response)
            prob = math.exp(choice.logprobs.content[0].logprob)  # Calculate probability
            probs.append(prob)
        else:
            continue
    
    highlevel_action_parser = build_highlevel_action_parser()
    # Initialize weighted counting dictionaries
    weighted_action_count = defaultdict(float)
    all_actions = {}

    action_list = list(action_set.action_set.keys())
    ## filter the responses list


    filtered_responses = []
    filtered_probs = []

    for prob, response in zip(probs, responses):
        # Flag to check if any action is found as substring
        contains_action = False
        for action in action_list:
            if action in response["content"]:
                contains_action = True
                break
        # If no action found in this response, add it to filtered list
        if contains_action:
            filtered_responses.append(response)
            filtered_probs.append(prob)
    
    print(filtered_responses)
    print(filtered_probs)

    responses = filtered_responses
    probs = filtered_probs

    # let llm to decide whether the trajectory finishes the task, if so, update the other sections
    
    # Process each response with its corresponding probability
    for response_dict, prob in zip(responses, probs):
        try:
            is_finished = response_dict["finished"]
            if is_finished == False:
                action = response_dict["content"]
                response_text = response_dict['natural_language_description']

                result = highlevel_action_parser.parse_string(action)
                result = result[0] if result else ""  # Convert to string
                if result not in all_actions:
                    all_actions[result] = {'natural_language_description': response_text}
                
                # Add weighted count
                weighted_action_count[result] += prob
            else:
                print(response_dict)
                response = "FINISH"
                response_text = "FINISH"
                result = "FINISH"

                if result not in all_actions:
                    all_actions[result] = {'natural_language_description': response_text}
                # Add weighted count
                weighted_action_count[result] += prob
        except Exception as e:
            pass
    
    # Get top actions based on weighted counts
    top_actions = sorted(weighted_action_count, 
                        key=weighted_action_count.get, 
                        reverse=True)[:branching_factor]
    
    total_weight = sum(weighted_action_count[action] for action in top_actions)
    
    # Create final weighted actions list
    updated_actions = []
    for action in top_actions:
        action_dict = all_actions[action].copy()
        action_dict['action'] = action
        action_dict['prob'] = weighted_action_count[action] / total_weight
        updated_actions.append(action_dict)
    
    # [{'action': "fill('113', 'dining table')", 'prob': 1.0}]
    return updated_actions

SYSTEM_PROMPT_TEMPLATE = \
"""
# Instructions
Review the current state of the page and all other information to find the best
possible next action and a natural language description of the action (example of natural language description is like)
"click the navbar button" or "select the portrait option" etc) to accomplish your goal.
Your answer will be interpreted and executed by a program, make sure to follow the formatting instructions.

Respond using valid JSON format, which can be parsed by python json.loads(), with keys:
- context (containing the action)
- natural_language_description
- finished (boolean: IMPORTANT - must be False if content field contains an action.
        Only set to True when NO more actions are needed and content field is empty)

Example response format:
{{
    "content": "action here",
    "natural_language_description": "description here",
    "finished": false  # Must be false because content contains an action
}}

# Rules for finished field:
- If content field contains any action: finished MUST be False
- Only set finished to True when:
    1. The goal is completely achieved
    2. No more actions are needed
    3. Content field is empty

Previous actions and action results are: {trajectory}

Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.

# Goal:
{goal}
"""

SYSTEM_PROMPT_TEMPLATE_WITH_IMAGES = \
"""
{SYSTEM_PROMPT_TEMPLATE}, and here are the input images
"""

USER_PROMPT_TEMPLATE = \
"""
{feature_text}

# Action Space
{action_set_description}

# Screenshot
The image provided is a screenshot of the current application state, corresponding to the Accessibility Tree above.

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click('12')```
"

Please analyze the screenshot and the Accessibility Tree to determine the next appropriate action. Refer to visual elements from the screenshot if relevant to your decision.
Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
"""

def generate_actions_with_observation(trajectory, goal, goal_images, openai_client: OpenAI, action_set, feature_text, screenshot,
                        branching_factor, log_folder, action_generation_model):
    
    if len(goal_images) == 0:
        system_msg = SYSTEM_PROMPT_TEMPLATE.format(trajectory=trajectory, goal=goal)
        messages = [{"role": "system", "content": system_msg}]
    else:
        system_msg = SYSTEM_PROMPT_TEMPLATE_WITH_IMAGES.format(trajectory=trajectory, goal=goal)
        messages = [{"role": "system", "content": system_msg}]
        content = []
        for image_i, image in enumerate(goal_images):
            image_base64 = base64.b64encode(image).decode('utf-8')
            content.extend([
                {"type": "text", "text": f"input image {image_i+1}: "},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}},
            ])
        messages.append({"role": "user", "content": content})
    
    action_set_description = action_set.describe(with_long_description=False, with_examples=True)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        feature_text=feature_text, 
        action_set_description=action_set_description
    )

    screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
    messages.append({"role": "user", "content": [
        {"type": "text", "text": user_prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_base64}", "detail": "high"}}
    ]})

    response = openai_client.chat.completions.create(
        model=action_generation_model,
        response_format= {"type": "json_object"},  # Enable JSON mode
        messages=messages,
        logprobs=True,
        n=min(branching_factor * 2, 20),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"action_gen_prompt_{timestamp}.txt"
    file_path = os.path.join(log_folder, 'prompt', filename)
    prompt_str = f"""SYSTEM PROMPT:\n{system_msg}\n\nUSER PROMPT:\n{user_prompt}"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf8') as file:
        file.write(prompt_str)

    filename = f"action_gen_res_{timestamp}.json"
    file_path = os.path.join(log_folder, 'prompt', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf8') as file:
        file.write(response.model_dump_json())

    actions = parse_actions_from_response(response, action_set, branching_factor)
    return actions

def parse_actions_from_response(response, action_set, branching_factor):
    # check whether the task is finished, based on is finished
    # action, description, is_finished

    # responses: list[str] = [x.message.content for x in response.choices]
    import json
    import math
    #responses: list[dict] = [json.loads(x.message.content) for x in response.choices]
    #probs = [math.exp(x.logprobs.content[0].logprob) for x in response.choices]

    # Parse responses and probabilities, skipping invalid JSON entries
    responses = []
    probs = []

    def is_valid_json(string):
        try:
            result = json.loads(string)
            if "content" in result and "natural_language_description" in result and "finished" in result:
                return True
            else:
                print("can be loaded into dictionary, but doesn't have all the required fields")
                return False
        except:
            print("cannot be loaded into dictionary")
            return False

    # add error handling
    for i, choice in enumerate(response.choices):
        if is_valid_json(choice.message.content):
            # Attempt to parse the response content as JSON
            parsed_response = json.loads(choice.message.content)
            # If successful, add the parsed response and associated probability
            responses.append(parsed_response)
            prob = math.exp(choice.logprobs.content[0].logprob)  # Calculate probability
            probs.append(prob)
        else:
            continue
    
    highlevel_action_parser = build_highlevel_action_parser()
    # Initialize weighted counting dictionaries
    weighted_action_count = defaultdict(float)
    all_actions = {}

    action_list = list(action_set.action_set.keys())
    ## filter the responses list


    filtered_responses = []
    filtered_probs = []

    for prob, response in zip(probs, responses):
        # Flag to check if any action is found as substring
        contains_action = False
        for action in action_list:
            if action in response["content"]:
                contains_action = True
                break
        # If no action found in this response, add it to filtered list
        if contains_action:
            filtered_responses.append(response)
            filtered_probs.append(prob)

    responses = filtered_responses
    probs = filtered_probs

    # let llm to decide whether the trajectory finishes the task, if so, update the other sections
    
    # Process each response with its corresponding probability
    for response_dict, prob in zip(responses, probs):
        try:
            is_finished = response_dict["finished"]
            if is_finished == False:
                action = response_dict["content"]
                response_text = response_dict['natural_language_description']

                result = highlevel_action_parser.parse_string(action)
                result = result[0] if result else ""  # Convert to string
                if result not in all_actions:
                    all_actions[result] = {'natural_language_description': response_text}
                
                # Add weighted count
                weighted_action_count[result] += prob
            else:
                print(response_dict)
                response = "FINISH"
                response_text = "FINISH"
                result = "FINISH"

                if result not in all_actions:
                    all_actions[result] = {'natural_language_description': response_text}
                # Add weighted count
                weighted_action_count[result] += prob
        except Exception as e:
            pass
    
    # Get top actions based on weighted counts
    top_actions = sorted(weighted_action_count, 
                        key=weighted_action_count.get, 
                        reverse=True)[:branching_factor]
    
    total_weight = sum(weighted_action_count[action] for action in top_actions)
    
    # Create final weighted actions list
    updated_actions = []
    for action in top_actions:
        action_dict = all_actions[action].copy()
        action_dict['action'] = action
        action_dict['prob'] = weighted_action_count[action] / total_weight
        updated_actions.append(action_dict)
    
    # [{'action': "fill('113', 'dining table')", 'prob': 1.0}]
    return updated_actions
