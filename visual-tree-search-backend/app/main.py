import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Core API Backend",
    # Disable automatic redirects for trailing slashes
    redirect_slashes=False
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI backend"}

# Import routers - do this after creating the app to avoid circular imports
from app.api.routes.hello import router as hello_router
from app.api.routes.sse import router as sse_router
from app.api.routes.websocket import router as ws_router

# Include routers from different modules
app.include_router(hello_router, prefix="/api/hello", tags=["hello"])
app.include_router(sse_router, prefix="/api/sse", tags=["sse"])
app.include_router(ws_router, prefix="/api/ws", tags=["websocket"])

# Import the WebSocket endpoint handler
from app.api.routes.websocket import websocket_endpoint

# Register the WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)