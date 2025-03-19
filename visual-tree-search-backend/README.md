# Backend
```
python run_demo_treesearch.py \
    --browser-mode chromium \
    --storage-state shopping.json \
    --starting-url "${WEBSITE_BASE_URL}:7770/" \
    --agent-type "SimpleSearchAgent" \
    --action_generation_model "gpt-4o-mini" \
    --goal "search running shoes, click on the first result" \
    --iterations 3 \
    --max_depth 3 \
    --search_algorithm bfs
```