# Jharkhand Societal Innovation & Collaboration Portal

An SIH 2026 MVP starter with a React/Vite frontend and FastAPI backend. It includes a responsive landing/dashboard experience, challenge browsing/submission, rule-based categorization and priority scoring, and a demo API.

## Requirements
- Node.js 18+
- Python 3.10+

## Run the backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Run the frontend
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite. The frontend calls `http://127.0.0.1:8000` by default. Set `VITE_API_URL` to override it.

## Important MVP notes
- This is a demo foundation, not a production deployment. The backend uses an in-memory store to keep setup simple; replace it with PostgreSQL models and migrations before deployment.
- Priority scoring and categorization are transparent rule-based heuristics, not a trained AI model.
- Sample challenges are clearly labelled demo records. Do not present them as official government data.
- Authentication, secure uploads, institutional matching, opportunity applications, audit persistence, and production privacy controls remain implementation tasks before real use.
