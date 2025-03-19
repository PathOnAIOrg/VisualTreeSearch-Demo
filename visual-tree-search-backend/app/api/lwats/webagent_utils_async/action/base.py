# copied and modified from https://github.com/ServiceNow/BrowserGym
import playwright.async_api
from abc import ABC, abstractmethod
import ast
import sys
import os
import importlib.util
import logging
from typing import Any, Callable, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class AbstractActionSet(ABC):
    def __init__(self, strict: bool = False):
        self.strict = strict

    @abstractmethod
    def describe(self, with_long_description: bool = True, with_examples: bool = True) -> str:
        """
        Returns a textual description of this action space.
        """

    @abstractmethod
    def example_action(self, abstract: bool) -> str:
        """
        Returns an example action as a string.
        """

    @abstractmethod
    def to_python_code(self, action) -> str:
        """
        Converts the given action to browsergym-compatible python code.

        Args:
            action: the action to convert.

        Returns:
            Executable python code that performs the action in a browsergym environment.
        """


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate Python code syntax using AST parser.
    
    Args:
        code: String containing Python code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        error_msg = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
        return False, error_msg
    except Exception as e:
        return False, f"Parsing error: {str(e)}"


def save_code_to_file(code: str, log_folder: str) -> str:
    """Save code to a file and return the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    code_logs_dir = os.path.join(log_folder, "code")
    os.makedirs(code_logs_dir, exist_ok=True)
    filename = f"code_{timestamp}.py"
    file_path = os.path.join(code_logs_dir, filename)
    
    header = f"""# Generated Code
# Timestamp: {datetime.now().isoformat()}
# File: {filename}
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n' + code)
    
    logger.info(f"Saved code to: {file_path}")
    return file_path


async def execute_python_code(
        code: str,
        page: playwright.async_api.Page,
        context,
        send_message_to_user: callable,
        report_infeasible_instructions: callable,
):
    """
    Executes Python code in a new context, including asynchronous code using `await`.

    Args:
        code: the Python code to execute, as a string.
        page: the playwright page that will be made accessible to the code.
        send_message_to_user: utility function that will be made accessible to the code.
        report_infeasible_instructions: utility function that will be made accessible to the code.
    """
    globals = {
        "page": page,
        "context": context,
        "send_message_to_user": send_message_to_user,
        "report_infeasible_instructions": report_infeasible_instructions,
    }

    # Format the code with proper indentation
    formatted_code = "\n".join("    " + line for line in code.splitlines())

    # Create the async function wrapper with the properly indented code
    wrapper = f"""async def __ex():
{formatted_code}"""

    # Execute the wrapped code
    exec_globals = {}
    exec(wrapper, globals, exec_globals)
    await exec_globals['__ex']()


async def execute_python_code_safely(
    code: str,
    page: 'playwright.async_api.Page',
    context: Any,
    log_folder: str,
    send_message_to_user: Optional[Callable[[str], None]] = None,
    report_infeasible_instructions: Optional[Callable[[str], None]] = None
) -> str:
    """Execute Python code from file with provided context."""
    
    # Save the code to a file
    file_path = save_code_to_file(code, log_folder)
    
    try:
        # Add the code directory to Python path
        sys.path.insert(0, os.path.dirname(file_path))
        
        # Import the module using importlib
        spec = importlib.util.spec_from_file_location("generated_code", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        
        # Set the global variables in the module
        module.page = page
        module.context = context
        module.send_message_to_user = send_message_to_user
        module.report_infeasible_instructions = report_infeasible_instructions
        
        # Execute the module
        await spec.loader.exec_module(module)
        
    except Exception as e:
        logger.error(f"Error executing code: {e}")
        raise
        
    finally:
        # Remove the directory from sys.path
        if os.path.dirname(file_path) in sys.path:
            sys.path.remove(os.path.dirname(file_path))
    
    return file_path

