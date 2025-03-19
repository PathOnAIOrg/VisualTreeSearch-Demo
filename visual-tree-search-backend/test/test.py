import asyncio
import json
import websockets
import logging

# Set up logging to see more details
logging.basicConfig(level=logging.INFO)

async def test_tree_search_websocket():
    search_id = "search_20250319_203804_831926"
    uri = f"ws://localhost:3000/tree-search-ws/{search_id}"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send a ping message
        await websocket.send(json.dumps({
            "type": "ping"
        }))
        
        # Wait for pong response
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # Start a search
        await websocket.send(json.dumps({
            "type": "start_search",  # Changed from search_agent_request to match expected type
            "agent_type": "SimpleSearchAgent",
            "starting_url": "http://128.105.145.205:7770/",
            "goal": "search running shoes, click on the first result",
            "search_algorithm": "bfs",
            "headless": True,
            "max_depth": 3
        }))
        
        # Set a timeout to prevent hanging indefinitely
        timeout = 120  # 2 minutes
        start_time = asyncio.get_event_loop().time()
        
        # Continuously receive messages with timeout
        while True:
            try:
                # Use wait_for to add timeout to recv
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining = max(0, timeout - elapsed)
                
                if remaining <= 0:
                    print("Timeout reached. No more messages received.")
                    break
                
                response = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                data = json.loads(response)
                print(f"Received: {data['type']}")
                
                # Print more details for certain message types
                if data["type"] in ["node_update", "trajectory_start", "trajectory_complete", "status_update", "tree_complete"]:
                    print(json.dumps(data, indent=2))
                
            except asyncio.TimeoutError:
                print("Timeout waiting for response from WebSocket")
                break
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.run(test_tree_search_websocket())