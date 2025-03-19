from pydantic import BaseModel
import math
import re
from ..webagent_utils_sync.evaluation.evaluators import parse_oai_logprob

import base64

class IsGoalFinished(BaseModel):
    goal_finished: bool
def goal_finished_evaluator(messages, openai_client, goal, screenshot, model='gpt-4o-mini'):
    system_message = """You are an AI assistant evaluating the progress of a web browsing task. Your role is to determine if the overall goal of the task has been accomplished based on the actions taken and the conversation history.

    Guidelines for determining if the goal is finished:
    1. Review the list of actions taken during the web browsing session.
    2. Compare these actions to the stated goal of the task.
    3. Consider if the necessary information has been found or if the required interactions have been completed.
    4. Look for indicators of task completion, such as finding specific information, completing a purchase, or submitting a form.
    5. If the last actions suggest that the main objective has been achieved, consider the goal finished.
    6. If there are clear next steps that haven't been taken, the goal may not be finished.

    Remember:
    - Web browsing tasks often involve multiple steps like searching, navigating pages, filling forms, or extracting information.
    - The goal is finished when all necessary actions to complete the task have been taken.
    - If the actions deviate significantly from the goal without resolution, the goal may not be finished.

    Respond with 'goal_finished: true' if you determine the goal has been accomplished, or 'goal_finished: false' if it's still in progress or incomplete."""

    base64_image = base64.b64encode(screenshot).decode('utf-8')
    # screenshot bytes
    new_response = openai_client.beta.chat.completions.parse(
        model=model,
        messages= [
                {"role": "system", "content": system_message},
                *messages,
                {"role": "user",
                 "content": [
                     {"type": "text", "text": f"The final screenshot is as in the image, and the goal is {goal}, Is the overall goal finished?"},
                     {"type": "image_url",
                      "image_url": {
                          "url": f"data:image/jpeg;base64,{base64_image}",
                          "detail": "high"
                      }
                      }
                 ]
                 },
            ],
        response_format=IsGoalFinished,
        logprobs=True,
    )
    message = new_response.choices[0].message.parsed
    confidence_score = parse_oai_logprob(new_response)

    goal_finished = message.goal_finished
    return goal_finished, confidence_score