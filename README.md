# AI-First CRM HCP Module

This repository is a complete Round 1 assignment submission for an AI-first Healthcare Professional CRM module. It focuses on the **Log Interaction Screen** for field representatives and includes both structured form entry and conversational AI entry.

## Stack

- Frontend: React, Redux Toolkit, Vite, Google Inter, Lucide icons
- Backend: Python, FastAPI, SQLAlchemy
- AI orchestration: LangGraph
- LLM: Groq `gemma2-9b-it` through `langchain-groq`
- Database: PostgreSQL through SQLAlchemy

## What The LangGraph Agent Does

The LangGraph agent routes field representative requests to the correct sales workflow tool, enriches interaction notes with the LLM, and returns a structured result that the CRM UI can render. The same agent powers the chat panel and the explicit tool buttons.

## Five LangGraph Tools

1. `log_interaction` - Creates an HCP interaction from structured form data or chat notes. It uses the LLM to summarize notes, extract topics/products, infer sentiment, and propose a next action.
2. `edit_interaction` - Updates an existing interaction or the latest HCP interaction when the representative corrects details after a call.
3. `get_hcp_profile` - Retrieves HCP profile details, preferences, and recent interaction history for call planning.
4. `suggest_next_best_action` - Recommends the next commercial action based on HCP profile, specialty, tier, and recent interactions.
5. `draft_follow_up` - Generates a compliant follow-up email draft grounded in the latest logged interaction.

Bonus tool: `compliance_review` checks the latest interaction for off-label, adverse event, sample, and patient-identifiable information signals.

## Next-Level Additions

- AI-derived objections and commitments
- Compliance flags and quality scoring
- HCP insights strip for demo storytelling
- API smoke tests
- Dockerfiles and one-command PowerShell demo startup
- Architecture docs and REST request collection

## Run Locally

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
```

Edit `backend/.env` and add your Groq API key:

```env
GROQ_API_KEY=your-token
GROQ_MODEL=gemma2-9b-it
```

Or use the helper:

```powershell
.\scripts\set-groq-key.ps1
```

Then run:

```bash
uvicorn app.main:app --reload --port 8000
```

Quick demo mode without Docker:

```powershell
.\scripts\start-demo.ps1 -UseSqlite
```

Backend docs:

```text
http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Demo Flow For The 10-15 Minute Video

1. Explain that the goal is a field representative screen for logging HCP interactions.
2. Show the HCP sidebar and select an HCP.
3. Log an interaction through the structured form.
4. Open the AI chat tab and type a natural note such as:

```text
I met Dr. Meera Rao today in person. She asked for more efficacy data on CardioFlow, mentioned formulary access concerns, and wants a follow-up next Tuesday.
```

5. Show the timeline update.
6. Run each LangGraph tool from the tool console:
   - Log Interaction
   - Edit Interaction
   - HCP Profile
   - Next Best Action
   - Follow-up Draft
   - Compliance Review
7. Briefly open `backend/app/ai.py` and explain the LangGraph routing plus the tool registry.
8. Briefly open `frontend/src/store/crmSlice.js` and explain Redux state management.
9. Submit the GitHub repository link in the Google Form from the assignment PDF.

See `demo/DEMO_SCRIPT.md` for a polished 10-15 minute narration outline.

## Notes

- The backend includes deterministic fallback behavior so the UI remains demoable if a Groq token is missing.
- For the final assignment recording, use a real Groq key so the `gemma2-9b-it` model is visibly part of the workflow.
- The app seeds demo HCPs automatically on backend startup.
