import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

from app.api.lwats.agents_async.SimpleSearchAgents.simple_search_agent import SimpleSearchAgent
from app.api.lwats.core_async.config import AgentConfig
from app.api.lwats.agents_async.SimpleSearchAgents.lats_node import LATSNode

@pytest.fixture
def mock_websocket():
    websocket = AsyncMock()
    websocket.send_json = AsyncMock()
    return websocket

@pytest.fixture
def mock_config():
    config = MagicMock(spec=AgentConfig)
    config.max_depth = 2  # Set a small max depth for testing
    config.search_algorithm = "bfs"
    config.evaluation_model = "gpt-4"
    config.browser_mode = "browserbase"
    config.headless = True
    config.storage_state = None
    config.log_folder = "test_logs"
    config.fullpage = False
    config.features = []
    config.elements_filter = []
    config.branching_factor = 2
    config.action_generation_model = "gpt-4"
    config.action_grounding_model = "gpt-4"
    return config

@pytest.fixture
def mock_playwright_manager():
    manager = AsyncMock()
    manager.get_page = AsyncMock()
    manager.close = AsyncMock()
    manager.get_live_browser_url = AsyncMock(return_value="http://test-url")
    return manager

@pytest.mark.asyncio
async def test_bfs_with_websocket_depth_limit(mock_websocket, mock_config, mock_playwright_manager):
    # Create a SimpleSearchAgent instance
    agent = SimpleSearchAgent(
        starting_url="http://test.com",
        messages=[],
        goal="test goal",
        images=[],
        playwright_manager=mock_playwright_manager,
        config=mock_config
    )

    # Create a simple tree structure for testing
    root = agent.root_node
    child1 = LATSNode(
        natural_language_description="child1",
        action="action1",
        prob=1.0,
        element=None,
        goal="test goal",
        parent=root
    )
    child2 = LATSNode(
        natural_language_description="child2",
        action="action2",
        prob=1.0,
        element=None,
        goal="test goal",
        parent=root
    )
    root.children = [child1, child2]

    # Mock the expand method to simulate node expansion
    async def mock_expand(node, websocket=None):
        if node.depth < mock_config.max_depth:
            new_child = LATSNode(
                natural_language_description=f"child{node.depth + 1}",
                action=f"action{node.depth + 1}",
                prob=1.0,
                element=None,
                goal="test goal",
                parent=node
            )
            node.children = [new_child]

    # Mock both expand and _reset_browser methods
    with patch.object(agent, 'expand', side_effect=mock_expand), \
         patch.object(agent, '_reset_browser', return_value="http://test-url"):
        # Run the bfs_with_websocket method
        result = await agent.bfs_with_websocket(mock_websocket)

        # Verify that the depth limit was respected
        # Check if any node beyond max_depth was processed
        depth_limit_messages = [
            call for call in mock_websocket.send_json.call_args_list
            if call[0][0].get("type") == "node_terminal" and 
               call[0][0].get("reason") == "depth_limit"
        ]
        
        assert len(depth_limit_messages) > 0, "No depth limit messages were sent"
        
        # Verify the structure of the tree
        def check_node_depth(node, expected_depth):
            assert node.depth <= mock_config.max_depth, f"Node at depth {node.depth} exceeds max_depth"
            for child in node.children:
                check_node_depth(child, expected_depth + 1)
        
        check_node_depth(root, 0) 