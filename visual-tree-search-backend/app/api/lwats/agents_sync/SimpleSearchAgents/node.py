import numpy as np

class Node:
    def __init__(self, state, goal, parent=None):
        self.state = state or {}
        self.parent = parent
        self.goal = goal
        self.children = []
        self.visits = 0
        self.value = 0
        self.depth = 0 if parent is None else parent.depth + 1
        self.is_terminal = False
        self.reward = 0
        self.exhausted = False

    ## added add_child
    def add_child(self, child_state):
        child = Node(child_state, self.goal, parent=self)
        self.children.append(child)
        return child

    ## added update
    def update(self, reward):
        self.visits += 1
        self.value += reward

    ## added uct score, instead of uct()
    def uct_score(self, c_param=1.41):
        if self.visits == 0:
            return float('inf')
        return (self.value / self.visits) + c_param * np.sqrt(np.log(self.parent.visits) / self.visits)

    ## added select best child
    def best_child(self):
        return max(self.children, key=lambda c: c.uct_score())

    def is_fully_expanded(self):
        return len(self.children) > 0 and all(child.visits > 0 for child in self.children)

    def __repr__(self):
        return f"Node(state={self.state}, value={self.value:.2f}, visits={self.visits}, depth={self.depth})"

