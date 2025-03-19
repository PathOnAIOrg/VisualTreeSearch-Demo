# Backend
## Run demo tree search
```
python run_demo_treesearch.py \
    --browser-mode chromium \
    --storage-state shopping.json \
    --starting-url "http://128.105.145.205:7770/" \
    --agent-type "SimpleSearchAgent" \
    --action_generation_model "gpt-4o-mini" \
    --goal "search running shoes, click on the first result" \
    --iterations 3 \
    --max_depth 3 \
    --search_algorithm bfs
```

## tree search api route
```
curl -X POST "http://localhost:3000/api/tree-search/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "SimpleSearchAgent",
    "browser_mode": "chromium",
    "storage_state": "shopping.json",
    "starting_url": "http://128.105.145.205:7770/",
    "action_generation_model": "gpt-4o-mini",
    "goal": "search running shoes, click on the first result",
    "iterations": 3,
    "max_depth": 3,
    "search_algorithm": "bfs",
    "headless": false
  }'
```