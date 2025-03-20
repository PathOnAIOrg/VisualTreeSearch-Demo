import asyncio
import json
import websockets
import logging
import uuid

# Set up logging to see more details
logging.basicConfig(level=logging.INFO)

async def test_websocket():
    uri = "ws://localhost:3000/ws"
    
    print(f"Connecting to {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send a ping message
        await websocket.send(json.dumps({
            "type": "ping"
        }))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # You can send other test messages here
        # For example, if the websocket supports it:
        await websocket.send(json.dumps({
            "type": "hello",
            "message": "Testing the websocket connection"
        }))
        
        # Set a timeout to prevent hanging indefinitely
        timeout = 60  # 1 minute
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
                print(f"Received: {response}")
                
                try:
                    data = json.loads(response)
                    print(f"Message type: {data.get('type', 'unknown')}")
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print("Received non-JSON message")
                
            except asyncio.TimeoutError:
                print("Timeout waiting for response from WebSocket")
                break
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.run(test_websocket())