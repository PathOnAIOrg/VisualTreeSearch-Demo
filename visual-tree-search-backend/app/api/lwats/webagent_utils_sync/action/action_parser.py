import re
from typing import Dict, List, Tuple, Any, Union, Literal
import ast

def parse_action(action_str: str) -> Tuple[str, List[Any], Dict[str, Any]]:
    """
    Executes an action string and returns a list of executed functions with their arguments.
    
    Args:
        action_str: String containing one or more function calls
        
    Returns:
        List of tuples containing (function_name, args_list)
        
    Examples:
        parse_action('click("123")')
        parse_action('fill("237", "example value")')
    """
    # Strip whitespace and handle empty strings
    action_str = action_str.strip()
    if not action_str:
        return []

    # Extract function name and arguments using regex
    match = re.match(r'(\w+)\((.*)\)$', action_str)
    if not match:
        raise ValueError(f"Invalid action format: {action_str}")

    func_name, args_str = match.groups()

    # Parse arguments handling both positional and keyword args
    args = []
    kwargs = {}
    
    if args_str:
    # Use a more sophisticated regex that preserves list structures
        pattern = r',\s*(?=[^[\]]*(?:\[|$))'
        parts = re.split(pattern, args_str)
        
        for part in parts:
            part = part.strip()
            if '=' in part:  # Keyword argument
                key, value = part.split('=', 1)
                key = key.strip()
                try:
                    kwargs[key] = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    raise ValueError(f"Invalid keyword argument format in: {part}")
            else:  # Positional argument
                try:
                    args.append(ast.literal_eval(part))
                except (SyntaxError, ValueError):
                    raise ValueError(f"Invalid argument format in: {part}")

    return (func_name, args, kwargs)

        
if __name__ == "__main__":    
    print(parse_action('noop(1000)'))
    """
    Examples:
        select_option('a48', "blue")
        select_option('c48', ["red", "green", "blue"])
    """
    print(parse_action('select_option("a48", "blue")'))
    print(parse_action('select_option("c48", ["red", "green", "blue"])'))

    """
    click('a51')
        click('b22', button="right")
        click('48', button="middle", modifiers=["Shift"])
    """
    print(parse_action('click("a51")'))
    print(parse_action('click("b22", button="right")'))
    print(parse_action('click("48", button="middle", modifiers=["Shift"])'))

    """
    upload_file("572", "my_receipt.pdf")
        upload_file("63", ["/home/bob/Documents/image.jpg", "/home/bob/Documents/file.zip"])
    """
    print(parse_action('upload_file("572", "my_receipt.pdf")'))
    print(parse_action('upload_file("63", ["/home/bob/Documents/image.jpg", "/home/bob/Documents/)file.zip"])'))

    """
    fill('237', 'example value')
        fill('45', "multi-line\\nexample")
        fill('a12', "example with \\"quotes\\"")
    """
    print(parse_action('fill("237", "example value")'))
    print(parse_action('fill("45", "multi-line\\nexample")'))
    print(parse_action('fill("a12", "example with \\"quotes\\"")'))

