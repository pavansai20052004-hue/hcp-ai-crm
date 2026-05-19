# Submission Checklist

## GitHub Repository

- Push the full `hcp-ai-crm` folder to one GitHub repository.
- Confirm the repository contains:
  - `frontend/`
  - `backend/`
  - `docker-compose.yml`
  - `README.md`
  - `.env.example`

## Required Runtime Proof

- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:5173`
- Groq model configured as `gemma2-9b-it`
- PostgreSQL running through `docker compose up -d db`

## Video Recording Flow

Target duration: 10-15 minutes.

1. Open the frontend and explain the HCP CRM Log Interaction Screen.
2. Select an HCP from the left sidebar.
3. Show structured form logging and submit one interaction.
4. Switch to AI Chat and log a natural language interaction.
5. Show that the interaction timeline updates.
6. Run all five LangGraph tools:
   - Log Interaction
   - Edit Interaction
   - HCP Profile
   - Next Best Action
   - Follow-up Draft
7. Open `backend/app/ai.py` and show the LangGraph graph plus tool registry.
8. Open `frontend/src/store/crmSlice.js` and show Redux Toolkit async flows.
9. Mention that Groq `gemma2-9b-it` is used through `langchain-groq`.
10. Submit the GitHub link and video link in the assignment form:

```text
https://forms.gle/mkgZPhtkFtnvLJCz7
```

