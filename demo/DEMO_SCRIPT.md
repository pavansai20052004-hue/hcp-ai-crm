# 10-15 Minute Recording Script

## 0:00-1:00 Opening

Introduce the project as an AI-first HCP CRM module for life-sciences field representatives. Mention the required stack: React, Redux, FastAPI, LangGraph, Groq `gemma2-9b-it`, and PostgreSQL.

## 1:00-3:00 HCP Workspace

Show the left-side HCP list, selected HCP context, specialty, tier, territory, preferred channel, and persona notes. Point out the insights strip for interaction count, quality score, compliance flags, and top topic.

## 3:00-5:00 Structured Logging

Use the form to log an in-person interaction. Include channel, interaction type, sentiment, products, topics, objections, commitments, and field notes. Submit and show the timeline update.

## 5:00-7:00 Conversational Logging

Switch to AI Chat and enter:

```text
Met Dr. Meera Rao today. She asked for approved efficacy data, raised access concerns, and wants a follow-up email next Tuesday.
```

Explain that LangGraph routes the message to `log_interaction` and the LLM enriches it.

## 7:00-10:00 Tool Console

Run each tool:

- Log
- Edit
- Profile
- Next Action
- Email
- Compliance

Explain what each output means and why it matters to field representatives.

## 10:00-13:00 Code Walkthrough

Open these files:

- `backend/app/ai.py` for LangGraph routing and tool functions.
- `backend/app/models.py` for the HCP and interaction data model.
- `frontend/src/store/crmSlice.js` for Redux async state management.
- `frontend/src/components/ToolConsole.jsx` for tool demos.

## 13:00-15:00 Close

Summarize that the system supports structured and conversational logging, compliance-aware AI enrichment, sales next-best-action guidance, and clear auditability.

