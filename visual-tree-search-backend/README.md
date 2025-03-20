# Backend
## 1. Run demo tree search
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

```
#AgentConfig(headless=False, browser_mode='chromium', storage_state='shopping.json', default_model='gpt-4o-mini', action_generation_model='gpt-4o-mini', feedback_model='gpt-4o-mini', planning_model='gpt-4o', action_grounding_model='gpt-4o', evaluation_model='gpt-4o', search_algorithm='bfs', exploration_weight=1.41, branching_factor=5, iterations=3, max_depth=3, num_simulations=100, features=['axtree'], fullpage=False, elements_filter='som', log_folder='log')
#AgentConfig(headless=False, browser_mode='chromium', storage_state='shopping.json', default_model='gpt-4o-mini', action_generation_model='gpt-4o-mini', feedback_model='gpt-4o-mini', planning_model='gpt-4o', action_grounding_model='gpt-4o', evaluation_model='gpt-4o', search_algorithm='dfs', exploration_weight=1.41, branching_factor=5, iterations=3, max_depth=3, num_simulations=100, features=['axtree'], fullpage=False, elements_filter='som', log_folder='log')
```

```
python run_demo_treesearch_async.py \
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

## 2. tree search api route
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

## 3. test websocket
```
just uvicorn app.main:app --host 0.0.0.0 --port 3000

python test/test-tree-search-ws.py
```