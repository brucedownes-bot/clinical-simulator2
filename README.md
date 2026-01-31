# Adaptive Clinical Decision Simulator

RAG-powered adaptive learning platform for Hospitalists.

## Quick Start

### 1. Import to Replit
- Click "Import from GitHub"
- Select this repository

### 2. Configure Secrets (🔒 in Replit sidebar)
```
OPENAI_API_KEY=sk-proj-YOUR_KEY
OPENAI_ORG_ID=org-vqF6oLvoV4GIIq4fmxwoqpHz
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
SUPABASE_ANON_KEY=eyJhbG...
DATABASE_URL=postgresql://...
DEBUG=true
ALLOWED_ORIGINS=https://YOUR-REPL.replit.app
```

### 3. Install & Run
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit `/api/docs` for API documentation.

## Documentation
- `QUICKSTART_DOWNES.md` - Setup guide
- `DEPLOYMENT.md` - Full deployment instructions
- `TESTING.md` - Test scenarios

## Architecture
- Backend: FastAPI + Python
- Database: Supabase (PostgreSQL + pgvector)
- AI: OpenAI GPT-4o + Embeddings
