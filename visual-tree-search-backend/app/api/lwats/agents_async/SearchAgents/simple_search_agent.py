from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from .tree_vis import better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .base_agent import BaseAgent

class SimpleSearchAgent(BaseAgent):
    async def run(self, websocket=None) -> List[Dict[str, Any]]:
        algorithm = self.config.search_algorithm.lower()
        
        if algorithm == "bfs":
            print("Starting BFS algorithm")
            return await self.bfs(websocket=websocket)
        elif algorithm == "dfs":
            print("Starting DFS algorithm")
            return await self.dfs(websocket)
        else:
            error_msg = f"Unsupported algorithm: {algorithm}"
            print(error_msg)
            if websocket:
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
            raise ValueError(error_msg)

    # TODO: first evaluate, then expansion, right now, it is first expansion, then evaluation
    async def bfs(self, websocket=None):
        queue = deque([self.root_node])
        queue_set = {self.root_node}  # Track nodes in queue
        best_score = float('-inf')
        best_path = None
        best_node = None
        visited = set()  # Track visited nodes to avoid cycles
        current_level = 0  # Track current level for BFS
        
        while queue:
            # Process all nodes at current level
            level_size = len(queue)
            current_level += 1
            level_nodes = []  # Store nodes at current level for later processing
            
            # First, expand all nodes at current level
            for _ in range(level_size):
                current_node = queue.popleft()
                queue_set.remove(current_node)  # Remove from queue tracking
                visited.add(current_node)
                
                # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
                # node expansion for the next level
                if not current_node.children and current_node.depth < self.config.max_depth:
                    ## during the node expansion process, reset browser for each node
                    live_browser_url, session_id = await self._reset_browser(websocket)
                    # await self.websocket_step_start(step=1, step_name="node_expansion", websocket=websocket)
                    await self.websocket_node_selection(current_node, websocket=websocket)
                    await self.node_expansion(current_node, websocket)
                    tree_data = self._get_tree_data()
                    
                    if websocket:
                        await self.websocket_tree_update(type="tree_update_node_expansion", websocket=websocket, tree_data=tree_data)
                    else:
                        print_entire_tree(self.root_node)
                
                # Store node for later processing
                level_nodes.append(current_node)
                
                # Add non-terminal children to queue for next level if they haven't reached max_depth
                for child in current_node.children:
                    if child not in visited and child not in queue_set and child.depth <= self.config.max_depth:
                        queue.append(child)
                        queue_set.add(child)  # Add to queue tracking

            # stage 2: node evaluation
            for current_node in level_nodes:
                # await self.websocket_step_start(step=2, step_name="node_evaluation", websocket=websocket)
                await self.node_evaluation(current_node)
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_evaluation", websocket=websocket, tree_data=tree_data)
                else:
                    print("after evaluation")
                    print_entire_tree(self.root_node)
                path = self.get_path_to_root(current_node)
                score = current_node.value
                
                # Update best path if this score is better
                if score > best_score:
                    best_score = score
                    best_path = path
                    best_node = current_node

                    
                print(f"Node {id(current_node)} score: {score}")
                
                # If we've found a satisfactory solution, return it
                if score >= 0.75:
                    print(f"Found satisfactory solution with score {score}")
                    
                    # Send completion update if websocket is provided
                    await self.websocket_search_complete("success", score, current_node.get_trajectory(), websocket=websocket) 
                    await self.playwright_manager.close()
                    
                    return current_node
            
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            print(f"Returning best path found with score {best_score}")
            
            # Send completion update if websocket is provided
            await self.websocket_search_complete("partial_success", best_score, best_node.get_trajectory(), websocket=websocket)
            await self.playwright_manager.close()
            
            return best_node
        
        # If no path was found at all
        print("No valid path found")
        
        # Send failure update if websocket is provided
        await self.websocket_search_complete("failure", 0, None, websocket=websocket)
        await self.playwright_manager.close()
        
        return None
        
    async def dfs(self, websocket=None):
        stack = [self.root_node]  # Use a list as a stack
        stack_set = {self.root_node}  # Track nodes in stack
        best_score = float('-inf')
        best_path = None
        best_node = None
        visited = set()  # Track visited nodes to avoid cycles
        
        while stack:
            # Get the top node from the stack
            current_node = stack.pop()
            stack_set.remove(current_node)  # Remove from stack tracking
            visited.add(current_node)
            
            # Expand current node if it hasn't been expanded yet and hasn't reached max_depth
            if not current_node.children and current_node.depth < self.config.max_depth:
                # Reset browser for each node expansion
                live_browser_url, session_id = await self._reset_browser(websocket)
                await self.websocket_node_selection(current_node, websocket=websocket)
                await self.node_expansion(current_node, websocket)
                tree_data = self._get_tree_data()
                
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_expansion", websocket=websocket, tree_data=tree_data)
                else:
                    print_entire_tree(self.root_node)
            
            # Node evaluation
            await self.node_evaluation(current_node)
            tree_data = self._get_tree_data()
            if websocket:
                await self.websocket_tree_update(type="tree_update_node_evaluation", websocket=websocket, tree_data=tree_data)
            else:
                print("after evaluation")
                print_entire_tree(self.root_node)
            
            path = self.get_path_to_root(current_node)
            score = current_node.value
            
            # Update best path if this score is better
            if score > best_score:
                best_score = score
                best_path = path
                best_node = current_node
                
            print(f"Node {id(current_node)} score: {score}")
            
            # If we've found a satisfactory solution, return it
            if score >= 0.75:
                print(f"Found satisfactory solution with score {score}")
                
                # Send completion update if websocket is provided
                await self.websocket_search_complete("success", score, current_node.get_trajectory(), websocket=websocket) 
                await self.playwright_manager.close()
                
                return current_node
            
            # Add children to stack in reverse order so that the first child is processed first
            # This maintains the left-to-right exploration order similar to BFS
            for child in reversed(current_node.children):
                if child not in visited and child not in stack_set and child.depth <= self.config.max_depth:
                    stack.append(child)
                    stack_set.add(child)  # Add to stack tracking
        
        # If we've exhausted all nodes and haven't found a perfect solution,
        # return the best path we found
        if best_path:
            print(f"Returning best path found with score {best_score}")
            
            # Send completion update if websocket is provided
            await self.websocket_search_complete("partial_success", best_score, best_node.get_trajectory(), websocket=websocket)
            await self.playwright_manager.close()
            
            return best_node
        
        # If no path was found at all
        print("No valid path found")
        
        # Send failure update if websocket is provided
        await self.websocket_search_complete("failure", 0, None, websocket=websocket)
        await self.playwright_manager.close()
        
        return None