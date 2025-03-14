import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from app.api.routes import hello, sse, websocket

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Core API Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGIN", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from different modules
app.include_router(hello.router, prefix="/api/hello", tags=["hello"])
app.include_router(sse.router, prefix="/api/sse", tags=["sse"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])

# Add WebSocket endpoint directly to the app
app.add_websocket_route("/ws", websocket.websocket_endpoint)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI backend"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)