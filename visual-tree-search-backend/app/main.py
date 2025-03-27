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
from app.api.routes.tree_websocket import router as tree_ws_router
from app.api.routes.tree_search import router as tree_search_router
from app.api.routes.tree_search_websocket import router as tree_search_ws_router
from app.api.routes.terminate_session import router as terminate_session_router
# Include routers from different modules
app.include_router(hello_router, prefix="/api/hello", tags=["hello"])
app.include_router(sse_router, prefix="/api/sse", tags=["sse"])
app.include_router(ws_router, prefix="/api/ws", tags=["websocket"])
app.include_router(tree_ws_router, prefix="/api/tree", tags=["tree"])
app.include_router(tree_search_router, prefix="/api/tree-search", tags=["tree-search"])
app.include_router(tree_search_ws_router, prefix="/api/tree-search-ws", tags=["tree-search-ws"])
app.include_router(terminate_session_router, prefix="/api/terminate-session", tags=["terminate-session"])
# Import the WebSocket endpoint handlers
from app.api.routes.websocket import websocket_endpoint
from app.api.routes.tree_websocket import tree_websocket_endpoint
from app.api.routes.tree_search_websocket import tree_search_websocket_endpoint
# Register the WebSocket endpoints
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.websocket("/tree-ws")
async def tree_websocket_route(websocket: WebSocket):
    await tree_websocket_endpoint(websocket)

@app.websocket("/tree-search-ws")
async def tree_search_websocket_route(websocket: WebSocket):
    await tree_search_websocket_endpoint(websocket)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)