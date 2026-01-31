# Quick Start - Downes Setup

## 🎯 Import to Replit

1. Go to [replit.com](https://replit.com)
2. Click "+ Create Repl"
3. Choose "Import from GitHub"
4. Paste your repository URL
5. Click "Import from GitHub"

## ⚙️ Configure Replit Secrets

Click 🔒 **Secrets** in Replit sidebar and add:

### Required Secrets:
```
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY
OPENAI_ORG_ID=org-vqF6oLvoV4GIIq4fmxwoqpHz
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres

DEBUG=true
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://YOUR-REPL-NAME.replit.app

CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K_RETRIEVAL=3
MIN_SIMILARITY_THRESHOLD=0.70
LEVEL_UP_THRESHOLD=8.0
LEVEL_DOWN_THRESHOLD=5.0
```

## 🗄️ Set Up Supabase

1. Go to [supabase.com](https://supabase.com/dashboard)
2. Organization: **Downes**
3. Create new project: `clinical-simulator`
4. Enable **pgvector** extension (Database → Extensions)
5. Run `database/schema.sql` in SQL Editor
6. Copy connection details to Secrets above

## 🚀 Run in Replit

Just click the **Run** button! 

Or in Shell:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit your Repl URL + `/api/docs` to see the API!

## ✅ Test It
```bash
# Upload a PDF
curl -X POST https://YOUR-REPL.replit.app/api/documents/upload \
  -H "Authorization: Bearer test-user-001" \
  -F "file=@test.pdf" \
  -F "title=Test Guideline"
```

## 📚 Next Steps

See `DEPLOYMENT.md` for full setup guide.
