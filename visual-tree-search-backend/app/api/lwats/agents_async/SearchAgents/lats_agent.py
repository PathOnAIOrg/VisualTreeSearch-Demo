from typing import Any, Optional, Tuple, List
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from .tree_vis import RED, better_print, print_trajectory, collect_all_nodes, GREEN, RESET, print_entire_tree
from .lats_node import LATSNode
from .base_agent import BaseAgent

class LATSAgent(BaseAgent):
    async def run(self, websocket=None) -> list[LATSNode]:
        if websocket:
            await websocket.send_json({
                "type": "search_status",
                "status": "started",
                "message": "Starting LATS search",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        best_node = await self.lats_search(websocket)
        print_trajectory(best_node)

    async def lats_search(self, websocket=None):
            terminal_nodes = []

            for i in range(self.config.iterations):
                await self.websocket_iteration_start(i, websocket=websocket)
                
                print(f"Iteration {i}...")

                # Step 1: Node Selection
                ## TODO: move websocket node selection into node_selection method
                print(f"{GREEN}Step 1: node selection{RESET}")
                await self.websocket_step_start(step=1, step_name="node_selection", websocket=websocket)
                node = await self.node_selection(self.root_node)
                await self.websocket_node_selection(node, websocket=websocket)

                if node is None:
                    print("All paths lead to terminal nodes with reward 0. Ending search.")
                    break

                # Step 2: Node Expansion
                print(f"{GREEN}Step 2: node expansion{RESET}")
                await self.websocket_step_start(step=2, step_name="node_expansion", websocket=websocket)
                await self.node_expansion(node, websocket)
                if node is None:
                    # all the nodes are terminal, stop the search
                    print(f"{RED}All nodes are terminal, stopping search{RESET}")
                    break
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_expansion", tree_data=tree_data)
                else:
                    print_entire_tree(self.root_node)


                # Step 3: Evaluation
                print(f"{GREEN}Step 3: node chilren evaluation{RESET}")
                await self.websocket_step_start(step=3, step_name="node_children_evaluation", websocket=websocket)
                await self.node_children_evaluation(node)
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_children_evaluation", tree_data=tree_data)
                else:
                    print("after evaluation")
                    print_entire_tree(self.root_node)


                # Step 4: Simulation
                print(f"{GREEN}Step 4: simulation{RESET}")
                await self.websocket_step_start(step=4, step_name="simulation", websocket=websocket)
                selected_node = max(node.children, key=lambda child: child.value)
                await self.websocket_node_selection(selected_node, websocket=websocket, type="node_selected_for_simulation")
                reward, terminal_node = await self.simulation(selected_node, max_depth=self.config.max_depth, num_simulations=1, websocket=websocket)
                terminal_nodes.append(terminal_node)
                await self.websocket_simulation_result(reward, terminal_node, websocket=websocket)

                if reward == 1:
                    return terminal_node

                # Step 5: Backpropagation
                print(f"{GREEN}Step 5: backpropagation{RESET}")
                await self.websocket_step_start(step=5, step_name="backpropagation", websocket=websocket)
                self.backpropagate(terminal_node, reward)
                tree_data = self._get_tree_data()
                if websocket:
                    await self.websocket_tree_update(type="tree_update_node_backpropagation", tree_data=tree_data)
                else:
                    print("after backpropagation")
                    print_entire_tree(self.root_node)

            # Find best node
            all_nodes_list = collect_all_nodes(self.root_node)
            all_nodes_list.extend(terminal_nodes)
            
            ## temp change: if reward is the same, choose the deeper node
            best_child = max(all_nodes_list, key=lambda x: (x.reward, x.depth))
            
            if best_child.reward == 1:
                print("Successful trajectory found")
            else:
                print("Unsuccessful trajectory found")
            await self.playwright_manager.close()
                
            return best_child if best_child is not None else self.root_node

    async def node_selection(self, node: LATSNode, websocket=None) -> Optional[LATSNode]:   
        if node.is_terminal:
            return None
        ## TODO; move this node selection logic from LATSNode to LATSAgent
        selected_node = node.get_best_leaf()
        await self.websocket_node_selection(selected_node, websocket=websocket)
        return selected_node