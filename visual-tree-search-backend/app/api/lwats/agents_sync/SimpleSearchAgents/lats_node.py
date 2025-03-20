import numpy as np
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel
import base64
from ...webagent_utils_sync.evaluation.feedback import Feedback

@dataclass
class Element:
    """Represents a DOM element with its properties."""
    text: str
    tag: str
    id: str
    title: str
    ariaLabel: str
    name: str
    value: str
    placeholder: str
    class_name: str  # Changed from 'class' as it's a reserved keyword
    role: str
    unique_selector: str
    selector_uniqueness_validated: bool

class Observation(BaseModel):
    text: str
    image: Optional[bytes] = None
    image_base64: Optional[str] = None

    def get_base64_image(self):
        if self.image_base64 is None:
            self.image_base64 = base64.b64encode(self.image).decode('utf-8')
        return self.image_base64

class LATSNode:
    """
    A node class for Language-based Action Tree Search (LATS).
    
    This class implements a tree structure for MCTS-like search algorithms,
    specifically designed for language-based action planning in UI interactions.
    
    Attributes:
        natural_language_description (str): Human-readable description of the action
        action (str): The actual action to be executed
        prob (float): Probability or confidence score for this action
        element (Element): DOM element associated with this action
        goal (str): The target goal state
        parent (Optional[LATSNode]): Parent node in the tree
        children (list[LATSNode]): Child nodes in the tree
        visits (int): Number of times this node has been visited
        value (float): Accumulated value/score of this node
        depth (int): Depth of this node in the tree
        is_terminal (bool): Whether this node is a terminal state
        reward (float): Reward received at this node
        exhausted (bool): Whether all children have been explored
        em (float): Exact match score for evaluation
    """
    
    def __init__(
        self,
        natural_language_description: str,
        action: str,
        prob: float,
        element: dict,  # Using dict instead of Element for backward compatibility
        goal: str,
        parent: Optional['LATSNode'] = None
    ) -> None:
        """
        Initialize a new LATSNode.
        
        Args:
            natural_language_description: Human-readable description of the action
            action: The actual action to be executed
            prob: Probability or confidence score for this action
            element: DOM element associated with this action
            goal: The target goal state
            parent: Parent node in the tree, if any
        """
        self.natural_language_description = natural_language_description
        self.action = action
        self.prob = prob
        self.element = element
        self.feedback = ''
        self.goal_finish_feedback: Optional[Feedback] = None
        self.parent = parent
        self.goal = goal
        self.children: list[LATSNode] = []
        self.visits = 0
        self.value = 0.0
        self.depth = 0 if parent is None else parent.depth + 1
        self.is_terminal = False
        self.reward = 0.0
        self.exhausted = False  # If all children are terminal
        self.em = 0.0  # Exact match, evaluation metric
        self.observation: Optional[Observation] = None

    def uct(self) -> float:
        """
        Calculate the UCT (Upper Confidence Bound for Trees) value for this node.
        
        Returns:
            float: The UCT value for this node. If the node has never been visited,
                  returns the node's current value.
        """
        if self.visits == 0:
            return self.value
        return self.value / self.visits + np.sqrt(2 * np.log(self.parent.visits) / self.visits)
    
    def get_best_leaf(self) -> 'LATSNode':
        unfinished_children = [c for c in self.children if not c.is_terminal]
        if not unfinished_children:
            return self

        best_child = max(unfinished_children, key=lambda x: x.uct())
        return best_child.get_best_leaf()
    
    def get_action_trajectory(self) -> list[dict]:
        trajectory = []
        node = self
        # exclude the root node
        while node.parent is not None:
            trajectory.append({
                "action": node.action,
                "natural_language_description": node.natural_language_description,
                "element": node.element
            })
            node = node.parent
        return trajectory[::-1]
    
    def get_trajectory(self) -> list[dict]:
        trajectory = []
        node = self
        # exclude the root node
        while node.parent is not None:
            trajectory.append({
                "natural_language_description": node.natural_language_description,
                "action": node.action
            })
            node = node.parent
        return trajectory[::-1]
    
    def add_child(self, child: 'LATSNode') -> None:
        self.children.append(child)
        child.parent = self
        child.depth = self.depth + 1

    def check_terminal(self) -> bool:
        if not self.children or all(child.is_terminal for child in self.children):
            self.is_terminal = True
            if self.parent:
                self.parent.check_terminal()

    def __str__(self) -> str:
        """
        Get a string representation of the node.
        
        Returns:
            str: A string describing the node's key attributes
        """
        return (f"Node(depth={self.depth}, value={self.value:.2f}, "
                f"visits={self.visits}, action={self.action}, "
                f"feedback={self.feedback})")

    def to_dict(self) -> dict:
        """
        Convert the node and its subtree to a dictionary representation.
        
        Returns:
            dict: A dictionary containing all node attributes and recursive
                  representations of parent and children nodes
        """
        return {
            'state': self.state,
            'question': self.question,
            'parent': self.parent.to_dict() if self.parent else None,
            'children': [child.to_dict() for child in self.children],
            'visits': self.visits,
            'value': self.value,
            'depth': self.depth,
            'is_terminal': self.is_terminal,
            'reward': self.reward,
            'em': self.em,
        }

    @property
    def state(self) -> dict:
        """
        Get the current state representation of the node.
        
        Returns:
            dict: A dictionary containing the node's state information
        """
        return {
            'natural_language_description': self.natural_language_description,
            'action': self.action,
            'prob': self.prob,
            'element': self.element
        }

    @property
    def question(self) -> str:
        """
        Get the goal/question associated with this node.
        
        Returns:
            str: The goal or question string
        """
        return self.goal