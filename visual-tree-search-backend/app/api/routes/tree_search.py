import asyncio
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
import json
import os
import threading
import multiprocessing
from datetime import datetime
import logging

from ..run_demo_treesearch import main as run_tree_search
from ..lwats.core.config import AgentConfig, filter_valid_config_args

router = APIRouter()

# Store results of tree search runs
search_results = {}
# Store process objects
search_processes = {}

def run_search_in_process(search_id: str, args_dict):
    """Run the tree search in a separate process"""
    try:
        # Create an args object similar to what argparse would create
        class Args:
            pass
        
        args = Args()
        for key, value in args_dict.items():
            setattr(args, key, value)
        
        # Update status to running
        search_results[search_id]["status"] = "running"
        
        # Debug: Print current working directory and storage_state path
        logging.info(f"Current working directory: {os.getcwd()}")
        logging.info(f"Storage state path: {args.storage_state}")
        logging.info(f"Storage state exists: {os.path.exists(args.storage_state)}")
        logging.info(f"Starting URL: {args.starting_url}")  # Log the starting URL
        
        # Run the search
        results = run_tree_search(args)
        
        # Update results
        search_results[search_id]["results"] = results
        search_results[search_id]["status"] = "completed"
        search_results[search_id]["completed_at"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        logging.error(f"Error in search process: {str(e)}")
        search_results[search_id]["status"] = "failed"
        search_results[search_id]["error"] = str(e)

@router.post("/run")
async def start_tree_search(
    background_tasks: BackgroundTasks,
    agent_type: str = "SimpleSearchAgent",
    starting_url: str = "http://128.105.145.205:7770/",
    goal: str = "search running shoes, click on the first result",
    images: Optional[str] = None,
    search_algorithm: str = "bfs",
    headless: bool = True,
    browser_mode: str = "chromium",
    storage_state: str = "shopping.json",
    action_generation_model: str = "gpt-4o-mini",
    evaluation_model: str = "gpt-4o",
    branching_factor: int = 5,
    max_depth: int = 3,
    iterations: int = 3
):
    """Start a tree search with the given parameters"""
    # Create a unique ID for this search
    search_id = f"search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Parse images
    image_list = [img.strip() for img in images.split(',')] if images else []
    
    # Debug: Print all possible locations for the file
    logging.info(f"Current working directory: {os.getcwd()}")
    possible_locations = [
        os.path.join(os.getcwd(), storage_state),
        os.path.join(os.path.dirname(os.getcwd()), storage_state),
        os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), storage_state),
        os.path.abspath(storage_state)
    ]
    
    for loc in possible_locations:
        logging.info(f"Checking location: {loc}, exists: {os.path.exists(loc)}")
    
    # Try to find the file in various locations
    storage_state_path = None
    for loc in possible_locations:
        if os.path.exists(loc):
            storage_state_path = loc
            break
    
    if storage_state_path:
        logging.info(f"Found storage_state at: {storage_state_path}")
    else:
        logging.warning(f"Could not find storage_state file '{storage_state}' in any expected location")
        # Create an empty storage state file as a fallback
        storage_state_path = os.path.join(os.getcwd(), "empty_storage.json")
        with open(storage_state_path, 'w') as f:
            f.write("{}")
        logging.info(f"Created empty storage state file at {storage_state_path}")
    
    # Log the starting URL to verify it's being set correctly
    logging.info(f"Setting starting URL to: {starting_url}")
    
    # Create args dictionary
    args_dict = {
        "agent_type": agent_type,
        "starting_url": starting_url,
        "goal": goal,
        "images": image_list,
        "search_algorithm": search_algorithm,
        "headless": headless,
        "browser_mode": browser_mode,
        "storage_state": storage_state_path,  # Use the found path
        "action_generation_model": action_generation_model,
        "evaluation_model": evaluation_model,
        "branching_factor": branching_factor,
        "max_depth": max_depth,
        "iterations": iterations
    }
    
    # Initialize the results entry
    search_results[search_id] = {
        "id": search_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "config": args_dict
    }
    
    # Start the search in a separate process
    process = threading.Thread(
        target=run_search_in_process,
        args=(search_id, args_dict),
        daemon=True
    )
    search_processes[search_id] = process
    process.start()
    
    return {
        "search_id": search_id,
        "status": "pending",
        "message": "Tree search started in the background"
    }

@router.get("/status/{search_id}")
async def get_search_status(search_id: str):
    """Get the status of a tree search"""
    if search_id not in search_results:
        raise HTTPException(status_code=404, detail="Search ID not found")
    
    # Check if process is still alive
    if search_id in search_processes:
        process = search_processes[search_id]
        if process.is_alive():
            search_results[search_id]["status"] = "running"
        elif search_results[search_id]["status"] == "pending":
            # Process ended but status wasn't updated
            search_results[search_id]["status"] = "failed"
            search_results[search_id]["error"] = "Process terminated unexpectedly"
    
    return search_results[search_id]

@router.get("/list")
async def list_searches():
    """List all tree searches"""
    return {
        "searches": [
            {
                "id": search_id,
                "status": search_results[search_id]["status"],
                "created_at": search_results[search_id]["created_at"],
                "completed_at": search_results[search_id].get("completed_at")
            }
            for search_id in search_results
        ]
    }

@router.post("/cancel/{search_id}")
async def cancel_search(search_id: str):
    """Cancel a running search"""
    if search_id not in search_results:
        raise HTTPException(status_code=404, detail="Search ID not found")
    
    if search_id in search_processes:
        process = search_processes[search_id]
        if process.is_alive():
            # We can't directly terminate a thread, but we can mark it as cancelled
            search_results[search_id]["status"] = "cancelled"
            return {"message": f"Search {search_id} has been marked for cancellation"}
        else:
            return {"message": f"Search {search_id} is not running"}
    
    return {"message": f"Search {search_id} process not found"} 