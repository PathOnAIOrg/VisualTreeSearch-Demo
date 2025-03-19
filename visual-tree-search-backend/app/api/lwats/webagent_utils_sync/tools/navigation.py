from .shared_utils import take_action
from .registry import ToolRegistry, Tool


def navigation(task_description, **kwargs):
    response = take_action(task_description, ["bid", "nav"], **kwargs)
    return response


def register_navigation_tool():
    ToolRegistry.register(Tool(
        name="navigation",
        func=navigation,
        description="Perform a web navigation task, including fill text, click, search, go to new page",
        parameters={
            "task_description": {
                "type": "string",
                "description": "The description of the web navigation task, including fill text, click, search, go to new page"
            }
        }
    ))