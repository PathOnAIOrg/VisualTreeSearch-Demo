"""Module for scoring and evaluating action trajectories using LLMs."""

import base64
import json
from typing import Any, Optional
from openai import OpenAI

SYSTEM_PROMPT = \
"""You are a helpful assistant. Your task is to provides evaluation on web task completion by evaluating the current state
against the desired goal. Analyze the provided trajectory and screenshot of the web page, return a JSON response with:
1. score (integer 0-10)
2. explanation (string)

Example format:
{
    "score": 8,
    "explanation": "The trajectory effectively achieves the goal with minimal steps",
}
"""

USER_PROMPT_TEMPLATE = \
"""Goal: {goal}

Trajectory:
{trajectory_str}

Please provide:
1. A score from 0-10 (where 10 is perfect execution)
2. A brief explanation of the score"""

def create_llm_prompt(trajectory: list[dict[str, Any]], goal: str) -> tuple[str, str]:
    """
    Creates a prompt for LLM scoring and processes trajectory information.
    
    Args:
        trajectory: List of dictionaries containing action and description
        goal: The goal of the trajectory
    
    Returns:
        tuple: (prompt string, reversed trajectory string)
    """
    trajectory_str = "\n".join(
        f"Step {i+1}: {action['natural_language_description']} (Action: {action['action']})"
        for i, action in enumerate(trajectory)
    )
    
    prompt = USER_PROMPT_TEMPLATE.format(
        goal=goal,
        trajectory_str=trajectory_str,
    )
    return prompt

def score_trajectory_with_openai(
    prompt: str,
    openai_client: OpenAI,
    model: str = "gpt-4o",
    screenshot: Optional[bytes] = None
) -> dict[str, Any]:
    """
    Uses OpenAI to score the trajectory based on the provided prompt.
    
    Args:
        prompt: The prompt to send to OpenAI
        openai_client: OpenAI client instance
        model: OpenAI model to use
        screenshot: Screenshot of the current page

    Returns:
        dict: Parsed response containing score and explanation
    """
    system_message = SYSTEM_PROMPT
    
    try:
        content = [
            {"type": "text", "text": prompt},
        ]
        if screenshot is not None:
            base64_image = base64.b64encode(screenshot).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}})

        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {
            "score": 0,
            "explanation": f"Error occurred: {str(e)}",
            "suggestions": ["Check API connection and try again"]
        }