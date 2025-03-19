# VisualTreeSearch

- **Frontend**
  - NextJS 14
  - TailwindCSS
  - Shadcn UI Components
  - **Deployment**
    - Vercel


- **Backend**
  - FastAPI
  - **Deployment**
    - AWS ECS


## Local Testing
### FastAPI Backend
```
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

### Frontend
in the .env file
```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:3000
```

```
npm run dev -- -p 3001
```

