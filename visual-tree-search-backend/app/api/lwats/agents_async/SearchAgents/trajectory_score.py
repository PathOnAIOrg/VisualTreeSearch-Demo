"""Module for scoring and evaluating action trajectories using LLMs."""

import base64
import json
import datetime
from typing import Any, Optional, List, Dict, TypedDict
from openai import OpenAI

class TrajectoryMetrics(TypedDict):
    """Structured metrics for trajectory evaluation."""
    overall_score: float
    efficiency_score: float
    accuracy_score: float
    robustness_score: float
    detailed_explanation: str
    improvement_suggestions: List[str]
    key_achievements: List[str]
    potential_issues: List[str]
    metadata: Dict[str, Any]

SYSTEM_PROMPT = \
"""You are an expert web task completion evaluator. Your task is to provide a comprehensive evaluation of web task completion
by analyzing the trajectory against the desired goal. Consider multiple aspects of the task execution and provide detailed feedback.

Analyze the provided trajectory and screenshot of the web page, return a JSON response with:
1. overall_score (float 0-10): Overall task completion score
2. efficiency_score (float 0-10): How well the task was completed (minimal steps, optimal path)
3. accuracy_score (float 0-10): How precisely the actions were executed
4. robustness_score (float 0-10): How well the solution handles edge cases
5. detailed_explanation (string): Comprehensive analysis of the execution
6. improvement_suggestions (list of strings): Specific ways to improve the solution
7. key_achievements (list of strings): Important milestones reached
8. potential_issues (list of strings): Areas that could be problematic

Example format:
{
    "overall_score": 8.5,
    "efficiency_score": 9.0,
    "accuracy_score": 8.0,
    "robustness_score": 7.5,
    "detailed_explanation": "The trajectory effectively achieves the goal with minimal steps...",
    "improvement_suggestions": ["Could have used more efficient selectors", "Consider adding error handling"],
    "key_achievements": ["Successfully logged in", "Found target element"],
    "potential_issues": ["No timeout handling", "Assumes specific page layout"]
}
"""

USER_PROMPT_TEMPLATE = \
"""Goal: {goal}

Trajectory:
{trajectory_str}

Current Page State:
{page_state}

Please provide a comprehensive evaluation of the task completion."""

def format_trajectory_step(step: Dict[str, Any], index: int) -> str:
    """Format a single trajectory step with detailed information."""
    return f"""Step {index}:
  Action: {step['action']}
  Description: {step['natural_language_description']}
  Target: {step.get('target', 'N/A')}
  Status: {step.get('status', 'completed')}
  Output: {step.get('output', 'N/A')}"""

def create_llm_prompt(
    trajectory: List[Dict[str, Any]], 
    goal: str,
    page_state: Optional[Dict[str, Any]] = None
) -> str:
    """
    Creates a prompt for LLM scoring and processes trajectory information.
    
    Args:
        trajectory: List of dictionaries containing action and description
        goal: The goal of the trajectory
        page_state: Optional dictionary containing current page state information
    
    Returns:
        str: Formatted prompt string
    """
    # Format trajectory steps with more detail
    trajectory_str = "\n\n".join(
        format_trajectory_step(step, i+1)
        for i, step in enumerate(trajectory)
    )
    
    # Format page state if available
    page_state_str = "No page state information available"
    if page_state:
        page_state_str = json.dumps(page_state, indent=2)
    
    prompt = USER_PROMPT_TEMPLATE.format(
        goal=goal,
        trajectory_str=trajectory_str,
        page_state=page_state_str
    )
    return prompt

def validate_evaluation(evaluation: Dict[str, Any]) -> bool:
    """Validate the evaluation output has all required fields and correct types."""
    required_fields = {
        'overall_score': (int, float),
        'efficiency_score': (int, float),
        'accuracy_score': (int, float),
        'robustness_score': (int, float),
        'detailed_explanation': str,
        'improvement_suggestions': list,
        'key_achievements': list,
        'potential_issues': list
    }
    
    for field, expected_type in required_fields.items():
        if field not in evaluation:
            return False
        if not isinstance(evaluation[field], expected_type):
            return False
        if isinstance(evaluation[field], (int, float)):
            if not 0 <= evaluation[field] <= 10:
                return False
    
    return True

def normalize_scores(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize all scores to be between 0 and 1."""
    score_fields = ['overall_score', 'efficiency_score', 'accuracy_score', 'robustness_score']
    for field in score_fields:
        if field in evaluation:
            evaluation[field] = evaluation[field] / 10.0
    return evaluation

def score_trajectory_with_openai(
    prompt: str,
    openai_client: OpenAI,
    model: str = "gpt-4o",
    screenshot: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Uses OpenAI to score the trajectory based on the provided prompt.
    
    Args:
        prompt: The prompt to send to OpenAI
        openai_client: OpenAI client instance
        model: OpenAI model to use
        screenshot: Screenshot of the current page

    Returns:
        dict: Parsed response containing comprehensive evaluation
    """
    system_message = SYSTEM_PROMPT
    
    try:
        content = [
            {"type": "text", "text": prompt},
        ]
        if screenshot is not None:
            base64_image = base64.b64encode(screenshot).decode('utf-8')
            content.append({
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}", 
                    "detail": "high"
                }
            })

        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"}
        )
        
        evaluation = json.loads(response.choices[0].message.content)
        
        # Validate evaluation
        if not validate_evaluation(evaluation):
            raise ValueError("Invalid evaluation format")
        
        # Normalize scores
        evaluation = normalize_scores(evaluation)
        
        # Add metadata
        evaluation["metadata"] = {
            "model_used": model,
            "timestamp": datetime.datetime.now().isoformat(),
            "has_screenshot": screenshot is not None
        }
        
        return evaluation
        
    except Exception as e:
        return {
            "overall_score": 0.0,
            "efficiency_score": 0.0,
            "accuracy_score": 0.0,
            "robustness_score": 0.0,
            "detailed_explanation": f"Error occurred during evaluation: {str(e)}",
            "improvement_suggestions": ["Check API connection and try again"],
            "key_achievements": [],
            "potential_issues": ["Evaluation failed"],
            "metadata": {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
        }