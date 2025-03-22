import time
import os
import logging
from openai import OpenAI
import base64
from ..utils.utils import encode_image
from pydantic import BaseModel

logger = logging.getLogger(__name__)
openai_client = OpenAI()


async def capture_post_action_feedback(page, action, goal, log_folder):
    # screenshot_path_post = os.path.join(log_folder, 'screenshots', 'screenshot_post.png')
    time.sleep(3)
    # page.screenshot(path=screenshot_path_post)
    # base64_image = encode_image(screenshot_path_post)
    screenshot_bytes = await page.screenshot()

    # Encode the bytes to base64
    base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
    prompt = f"""
    After we take action {action}, a screenshot was captured.

    # Screenshot description:
    The image provided is a screenshot of the application state after the action was performed.

    # The original goal:
    {goal}

    Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user",
             "content": [
                 {"type": "text", "text": prompt},
                 {"type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}",
                      "detail": "high"
                  }
                  }
             ]
             },
        ],
    )

    return response.choices[0].message.content


class Feedback(BaseModel):
    is_done: bool
    explanation: str

FEEDBACK_SYSTEM_PROMPT_TEMPLATE = \
"""You are a helpful assitant. Given a goal, a description of the action just taken, a screenshot of the web page after the action was taken, your task is to provides feedback on web task completion by evaluating the current state against the desired goal."""

FEEDBACK_USER_PROMPT_TEMPLATE = \
"""
# The goal:
{goal}

# The action description:
{action_description}

Based on the screenshot of the web page, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant."""

async def generate_feedback_with_screenshot(goal, action_description, screenshot, model):
    system_prompt = FEEDBACK_SYSTEM_PROMPT_TEMPLATE
    user_prompt = FEEDBACK_USER_PROMPT_TEMPLATE.format(goal=goal, action_description=action_description)
    base64_image = base64.b64encode(screenshot).decode('utf-8')
    response = openai_client.beta.chat.completions.parse(
        model=model,
        response_format=Feedback,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                ]
            },
        ],
    )
    feedback = response.choices[0].message.parsed
    return feedback