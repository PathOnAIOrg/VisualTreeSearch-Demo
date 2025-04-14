"""Utilities for visualizing LATS tree structures."""

from typing import Optional
from .lats_node import LATSNode

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def collect_all_nodes(node: LATSNode) -> list[LATSNode]:
    """
    Recursively collect all nodes starting from the given node.
    
    Args:
        node: The root node to start collection from
        
    Returns:
        list[LATSNode]: List of all nodes in the tree
    """
    nodes = [node]
    for child in node.children:
        nodes.extend(collect_all_nodes(child))
    return nodes

def better_print(node: LATSNode, level: int = 0, selected_node: Optional[LATSNode] = None) -> None:
    """
    Print tree structure recursively with indentation, showing node statistics.

    Args:
        node: The node to print
        level: Current indentation level (default=0)
        selected_node: The currently selected node to highlight
    """
    indent = "    " * level

    action = node.action if node.action is not None else 'None'
    if isinstance(action, str):
        action = action.replace('\n', '')

    visits = f"visits: {node.visits}"
    value = f"value: {node.value:.3f}" if hasattr(node, 'value') else "value: N/A"
    reward = f"reward: {node.reward:.3f}" if hasattr(node, 'reward') else "reward: N/A"
    stats = f"[{visits}, {value}, {reward}]"

    if node == selected_node:
        print(f"{indent}├── Level {level}: {GREEN}{action}{RESET} {stats}  ← Selected")
    else:
        print(f"{indent}├── Level {level}: {action} {stats}")

    for child in node.children:
        better_print(child, level + 1, selected_node)

def print_trajectory(terminal_node: LATSNode) -> None:
    """
    Print the single path from a terminal node to the root.
    
    Args:
        terminal_node: The leaf node to start the trajectory from
    """
    path = []
    current = terminal_node
    while current is not None:
        path.append(current)
        current = current.parent
    
    for level, node in enumerate(reversed(path)):
        indent = "    " * level
        action = node.action
        
        visits = f"visits: {node.visits}"
        value = f"value: {node.value:.3f}" if hasattr(node, 'value') else "value: N/A"
        reward = f"reward: {node.reward:.3f}" if hasattr(node, 'reward') else "reward: N/A"
        is_terminal = f"terminal: {node.is_terminal}"
        feedback = f"feedback: {node.feedback if node.feedback else 'N/A'}"
        stats = f"[{visits}, {value}, {reward}, {is_terminal}, {feedback}]"
        
        indicator = ""
        if node == terminal_node:
            indicator = "← Terminal"
        elif not hasattr(node, 'parent') or node.parent is None:
            indicator = "(Root)"
        
        print(f"{indent}├── Level {level}: {GREEN}{action}{RESET} {stats} {indicator}")

def print_entire_tree(root: LATSNode) -> None:
    """
    Print the entire tree structure starting from the root node.
    
    Args:
        root: The root node of the tree to print
    """
    def _print_subtree(node: LATSNode, level: int, prefix: str, is_last: bool) -> None:
        # Prepare the current line's prefix
        current_prefix = prefix + ("└── " if is_last else "├── ")
        
        # Prepare node statistics
        action = node.action
        node_id = f"id: {id(node)}"
        visits = f"visits: {node.visits}"
        value = f"value: {node.value:.3f}" if hasattr(node, 'value') else "value: N/A"
        reward = f"reward: {node.reward:.3f}" if hasattr(node, 'reward') else "reward: N/A"
        is_terminal = f"terminal: {node.is_terminal}"
        feedback = f"feedback: {node.feedback if node.feedback else 'N/A'}"
        stats = f"[{visits}, {value}, {reward}, {is_terminal}, {feedback}]"
        
        # Add indicator for root or terminal nodes
        indicator = ""
        if not node.children:
            indicator = "← Terminal"
        elif level == 0:
            indicator = "(Root)"
        
        # Print the current node
        print(f"{current_prefix}{node_id} Level {level}: {GREEN}{action}{RESET} {stats} {indicator}")
        
        # Prepare the prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")
        
        # Sort children by some criteria (e.g., visits) if desired
        children = sorted(node.children, key=lambda x: x.visits, reverse=True) if node.children else []
        
        # Recursively print all children
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            _print_subtree(child, level + 1, child_prefix, is_last_child)
    
    # Start the recursive printing from the root
    _print_subtree(root, 0, "", True)