# Backend
## 1. Run demo tree search
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


## 2. test websocket
```
uvicorn app.main:app --host 0.0.0.0 --port 3000

python test/test-tree-search-ws.py
```

## 3. end-to-end test with frontend
```
backend: uvicorn app.main:app --host 0.0.0.0 --port 3000
frontend: npm run dev -- -p 3001
then go to http://localhost:3001/tree-search-playground
to test the message passing from the backend to the frontend
```

## 4. async browserbase mode
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