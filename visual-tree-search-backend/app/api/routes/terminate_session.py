# terminate browser session session
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from browserbase import Browserbase
from playwright.async_api import async_playwright
import os

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

router = APIRouter()

@router.post("/{session_id}")
async def terminate_session(session_id: str):
    try:
        # Initialize the Browserbase client
        bb = Browserbase(api_key=API_KEY)

        # Update the session's status to request release
        bb.sessions.update(
            session_id,
            project_id=PROJECT_ID,
            status="REQUEST_RELEASE"
        )

        return {"status": "success", "message": f"Session {session_id} termination requested"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))