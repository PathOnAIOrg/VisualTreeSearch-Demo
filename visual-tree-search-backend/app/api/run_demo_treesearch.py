import argparse
from dotenv import load_dotenv

from lwats.core.config import AgentConfig, add_agent_config_arguments, filter_valid_config_args
load_dotenv()
from lwats.core.agent_factory import setup_search_agent

def main(args):
    agent_config = AgentConfig(**filter_valid_config_args(args.__dict__))
    agent, playwright_manager = setup_search_agent(
        agent_type=args.agent_type,
        starting_url=args.starting_url,
        goal=args.goal,
        images=args.images,
        agent_config=agent_config
    )
    
    # Run the search
    results = agent.run()
    print(results)
    
    # Close the playwright_manager when done
    playwright_manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web agent with specified configuration")
    parser.add_argument("--agent-type", type=str, default="LATSAgent",
                    help="Type of agent to use (default: LATSAgent)")
    # Task
    parser.add_argument("--starting-url", type=str, default="http://128.105.146.96:7770/",
                        help="Starting URL for the web agent")
    parser.add_argument("--goal", type=str, default="search running shoes, click on the first result",
                        help="Goal for the web agent to accomplish")
    parser.add_argument("--images", type=str, default="",
                        help="Comma-separated paths to image files (e.g., 'path1.jpg,path2.jpg')")

    add_agent_config_arguments(parser)
    args = parser.parse_args()
    args.images = [img.strip() for img in args.images.split(',')] if args.images else []
    main(args)