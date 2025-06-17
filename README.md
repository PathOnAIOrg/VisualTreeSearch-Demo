# VisualTreeSearch

A powerful web agent visualization tool that helps you understand and analyze web automation processes through visual tree search.

## News
* 06/16/2025 - "VisualTreeSearch: Understanding Web Agent Test-time Scaling" was accepted by ECML-PKDD 2025.
* 04/28/2025 - Released Open Source Repo: [visual tree search](https://github.com/PathOnAIOrg/VisualTreeSearch-Demo).


## 🌐 Live Demo

[![Watch the video](https://img.youtube.com/vi/stRNDePQGV0/hqdefault.jpg)](https://www.youtube.com/embed/stRNDePQGV0)

Visit our live demo at: [visual-tree-search.pathonai.org](https://visual-tree-search.pathonai.org)

## 🌟 Features

- Interactive visualization of web agent actions
- Real-time tree search visualization
- Modern and responsive UI
- Comprehensive web automation analysis

## 🛠️ Tech Stack

### Frontend
- **Framework**: NextJS 14
- **Styling**: TailwindCSS
- **UI Components**: Shadcn UI
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI
- **Deployment**: AWS ECS

### Browser Service
- **Framework**: FastAPI
- **Deployment**: AWS ECS
- **Browser Engine**: Chromium (via Playwright)

### State Reset
- **Framework**: FastAPI
- **Deployment**: AWS EC2
- **Database Access**: SQLAlchemy ORM connecting to MariaDB (using MySQL-compatible interface)

## 🚀 Getting Started

### Prerequisites
- Node.js (Latest LTS version)
- Python 3.8+
- npm or yarn
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/PathOnAI/VisualTreeSearch-Demo.git
cd VisualTreeSearch-Demo
```

2. Backend Setup
```bash
# Navigate to backend directory
cd visual-tree-search-backend

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install uvicorn[standard]  # Install uvicorn with standard extras
```

3. Frontend Setup
```bash
# Navigate to frontend directory
cd ../visual-tree-search-app

# Install dependencies
npm install

# Create .env file
echo "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:3000" > .env
```

### Local Development

#### Backend
1. Navigate to backend directory:
```bash
cd visual-tree-search-backend
```

2. Activate virtual environment (if not already activated):
```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Run the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

Note: The `--reload` flag enables auto-reload when code changes are detected. Remove it in production.

#### Frontend
1. Open a new terminal and navigate to frontend directory:
```bash
cd visual-tree-search-app
```

2. Start the development server:
```bash
npm run dev -- -p 3001
```

The application should now be running at:
- Frontend: http://localhost:3001
- Backend: http://localhost:3000

## 📝 Project Structure

```
VisualTreeSearch-Demo/
├── visual-tree-search-app/        # Frontend application
│   ├── src/                      # Source code
│   ├── public/                   # Static files
│   └── package.json             # Frontend dependencies
├── visual-tree-search-backend/    # Backend API service
│   ├── app/                     # Backend source code
│   ├── requirements.txt         # Backend dependencies
│   └── test/                    # Test files
├── visual-tree-search-browser-service/  # Browser automation service
└── visual-tree-search-state-reset/     # State management service
```


