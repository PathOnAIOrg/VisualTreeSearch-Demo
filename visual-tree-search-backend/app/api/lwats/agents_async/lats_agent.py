    def _get_trajectory_data(self, terminal_node: LATSNode):
        """Get trajectory data in a format suitable for visualization
        
        Args:
            terminal_node: The leaf node to start the trajectory from
            
        Returns:
            list: List of node data dictionaries representing the trajectory
        """
        trajectory_data = []
        path = []
        
        # Collect path from terminal to root
        current = terminal_node
        while current is not None:
            path.append(current)
            current = current.parent
            
        # Process nodes in order from root to terminal
        for level, node in enumerate(reversed(path)):
            node_data = {
                "id": id(node),
                "level": level,
                "action": node.action if node.action else "ROOT",
                "description": node.natural_language_description,
                "visits": node.visits,
                "value": float(f"{node.value:.3f}") if hasattr(node, 'value') else None,
                "reward": float(f"{node.reward:.3f}") if hasattr(node, 'reward') else None,
                "is_terminal": node.is_terminal,
                "feedback": node.feedback if hasattr(node, 'feedback') else None,
                "is_root": not hasattr(node, 'parent') or node.parent is None,
                "is_terminal_node": node == terminal_node
            }
            trajectory_data.append(node_data)
            
        return trajectory_data 