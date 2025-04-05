# Backend
## 1. test playwright_manager
```
cd visual-tree-search-backend/app/api/lwats/webagent_utils_async/utils
python playwright_manager.py
```
also we use this script to renew the cookies store in file `app/api/shopping.json`

## 2. Run demo tree search
chromium mode
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

browserbase mode
```
python run_demo_treesearch_async.py \
    --browser-mode browserbase \
    --storage-state shopping.json \
    --starting-url "http://128.105.145.205:7770/" \
    --agent-type "SimpleSearchAgent" \
    --action_generation_model "gpt-4o-mini" \
    --goal "search running shoes, click on the first result" \
    --iterations 3 \
    --max_depth 3 \
    --search_algorithm bfs
```


## 3. test websocket
```
uvicorn app.main:app --host 0.0.0.0 --port 3000

python test/test-tree-search-ws.py
```

## 4. end-to-end test with frontend
```
backend: uvicorn app.main:app --host 0.0.0.0 --port 3000
frontend: npm run dev -- -p 3001
then go to http://localhost:3001/tree-search-playground
to test the message passing from the backend to the frontend
```



## 5. terminate session from backend
```
curl -X POST http://localhost:3000/api/terminate-session/647f4021-2402-4733-84a3-255f0d20c151
{"status":"success","message":"Session 647f4021-2402-4733-84a3-255f0d20c151 termination requested"}
```

## 6. Add more search agent
```
python run_demo_treesearch_async.py \
    --browser-mode chromium \
    --storage-state shopping.json \
    --starting-url "http://128.105.145.205:7770/" \
    --agent-type "LATSAgent" \
    --action_generation_model "gpt-4o-mini" \
    --goal "search running shoes, click on the first result" \
    --iterations 3 \
    --max_depth 3
```

```
python run_demo_treesearch_async.py \
    --browser-mode chromium \
    --storage-state shopping.json \
    --starting-url "http://128.105.145.205:7770/" \
    --agent-type "MCTSAgent" \
    --action_generation_model "gpt-4o-mini" \
    --goal "search running shoes, click on the first result" \
    --iterations 3 \
    --max_depth 3
```

## 7. Add LATS agent
* test run_demo_treesearch_async.py
* test web socket
```
uvicorn app.main:app --host 0.0.0.0 --port 3000
python test/test-tree-search-ws-lats.py
```

## 7. Add MCTS agent
* test run_demo_treesearch_async.py
* test web socket
```
uvicorn app.main:app --host 0.0.0.0 --port 3000
python test/test-tree-search-ws-mcts.py
```