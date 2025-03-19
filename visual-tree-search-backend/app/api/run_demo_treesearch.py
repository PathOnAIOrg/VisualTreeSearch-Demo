import argparse
from dotenv import load_dotenv
import json
import logging

from .lwats.core.config import AgentConfig, add_agent_config_arguments, filter_valid_config_args
load_dotenv()
from .lwats.core.agent_factory import setup_search_agent

def main(args):
    # Log the arguments to help debug
    logging.info(f"Running tree search with args: {args.__dict__}")
    
    # Ensure starting_url is set correctly
    if not hasattr(args, 'starting_url') or not args.starting_url:
        logging.error("starting_url is not set or is empty")
        return {"error": "starting_url is required"}
    
    logging.info(f"Using starting URL: {args.starting_url}")
    
    agent_config = AgentConfig(**filter_valid_config_args(args.__dict__))
    agent, playwright_manager = setup_search_agent(
        agent_type=args.agent_type,
        starting_url=args.starting_url,
        goal=args.goal,
        images=args.images,
        agent_config=agent_config
    )
    print(agent_config)
    
    # Run the search
    results = agent.run()
    
    # Close the playwright_manager when done
    playwright_manager.close()
    
    return results

if __name__ == "__main__":
    # When running as a script, we need to use absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.api.lwats.core.config import AgentConfig, add_agent_config_arguments, filter_valid_config_args
    from app.api.lwats.core.agent_factory import setup_search_agent
    
    parser = argparse.ArgumentParser(description="Run web agent with specified configuration")
    parser.add_argument("--agent-type", type=str, default="LATSAgent",
                    help="Type of agent to use (default: LATSAgent)")
    # Task
    parser.add_argument("--starting-url", type=str, default="http://128.105.145.205:7770/",
                        help="Starting URL for the web agent")
    parser.add_argument("--goal", type=str, default="search running shoes, click on the first result",
                        help="Goal for the web agent to accomplish")
    parser.add_argument("--images", type=str, default="",
                        help="Comma-separated paths to image files (e.g., 'path1.jpg,path2.jpg')")

    add_agent_config_arguments(parser)
    args = parser.parse_args()
    args.images = [img.strip() for img in args.images.split(',')] if args.images else []
    results = main(args)
    print(results)