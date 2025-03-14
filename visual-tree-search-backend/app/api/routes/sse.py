import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

# Store active SSE connections (using a simple list for the example)
clients: List[asyncio.Queue] = []

# Track the ping task
ping_task = None

async def send_event_to_all(event_data: Dict[str, Any]):
    """Send an event to all connected clients"""
    for queue in clients:
        await queue.put(event_data)

async def ping_clients():
    """Send a ping to all clients every second"""
    while True:
        if clients:
            event_data = {
                "type": "ping",
                "message": "Server heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_event_to_all(event_data)
            logging.info(f"Sent ping to {len(clients)} clients")
        await asyncio.sleep(1)

async def sse_generator(request: Request, client_queue: asyncio.Queue):
    """Generate SSE events"""
    try:
        while True:
            if await request.is_disconnected():
                break
            
            # Get message from the queue
            message = await client_queue.get()
            
            # Convert message to string if it's a dict
            if isinstance(message, dict):
                message = json.dumps(message)
            
            # Send the event
            yield f"data: {message}\n\n"
    finally:
        # Remove client when disconnected
        if client_queue in clients:
            clients.remove(client_queue)
        logging.info(f"Client disconnected - remaining clients: {len(clients)}")

@router.get("/events")
async def sse_endpoint(request: Request):
    """SSE endpoint that sends events to clients"""
    # Client connection queue
    client_queue = asyncio.Queue()
    clients.append(client_queue)
    
    # Start ping task if not already running
    global ping_task
    if ping_task is None or ping_task.done():
        ping_task = asyncio.create_task(ping_clients())
    
    logging.info(f"Client connected - total clients: {len(clients)}")
    
    # Initial connection message
    await client_queue.put({
        "type": "connection",
        "message": "Connected to SSE"
    })

    # Use StreamingResponse for SSE
    return StreamingResponse(
        sse_generator(request, client_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/status")
async def sse_status():
    """Get SSE connection status"""
    return {
        "active": len(clients),
        "status": "running"
    }