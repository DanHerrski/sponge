# Sprint Plan: Bet 2 — Content Ingestion & Engagement Surfaces (Weeks 7–9)

**Goal:** Enable document uploads, add Nugget Inbox + Node Detail Drawer, and implement onboarding.
**Capacity assumption:** 1 full-stack engineer, 5 dev-days per week.
**Prerequisite:** Bet 1 steel thread complete and demo-ready.

---

## Week 7 — Upload Ingestion Pipeline

**Theme:** Build the backend pipeline to accept documents, parse them, and feed nuggets into the graph.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | 9.1 FileStore abstraction: `save`, `get`, `delete` with local filesystem backend | E9 | Interface defined; local implementation stores/retrieves files |
| Mon | 9.2 Text parser: extract plain text from .txt and .docx files | E9 | Parser returns clean text from both formats |
| Tue | 9.3 Semantic chunker: split text into paragraph/topic-based chunks | E9 | Long doc splits into 5–15 coherent chunks; short doc stays as 1–2 chunks |
| Wed–Thu | 9.4 `POST /upload` endpoint: accept file, parse, chunk, run extraction pipeline per chunk | E9 | Endpoint accepts multipart file, returns nuggets with document provenance |
| Fri | 9.5 Upload response composer: summarize findings, top 3 nuggets + 3 deep-dive options | E9 | Response matches spec §10.3 format: "I found X ideas, Y stories" + choices |

**Week 7 exit criteria:** Backend accepts .txt/.docx uploads, parses and chunks content, extracts nuggets with document provenance, and returns a structured summary response.

---

## Week 8 — Upload UI + Nugget Inbox

**Theme:** Connect upload to the frontend and build the inbox for nugget management.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | 9.6 Upload button in frontend UI, display upload response in chat | E9 | User selects file → upload fires → response renders in chat with nuggets |
| Tue | Nugget Inbox component: list view with score sort, type filter, keyword search | New | Inbox shows all session nuggets; sort/filter/search work |
| Wed | `GET /nuggets?session_id=X` endpoint: return all nuggets sorted by score | New | Returns nuggets array with all fields; supports type filter query param |
| Wed | `POST /nugget/:id/status` endpoint: update status (New → Explored / Parked) | E9 | Status updates persist; reflected in inbox |
| Thu | Inbox status badges + action buttons: mark as Explored, Park, Double-click to explore | New | Status badges colored; click updates status; "Explore" sets next question |
| Fri | Inbox ↔ Chat integration: clicking "Explore" in inbox sets next question in chat | New | "Explore now" on any nugget puts its top question into the chat |

**Week 8 exit criteria:** Uploads work end-to-end in the UI. Nugget Inbox displays all session nuggets with sort, filter, search, and status management.

---

## Week 9 — Node Detail Drawer + Onboarding

**Theme:** Finish the engagement surfaces — detail inspection and session context setup.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon–Tue | Node Detail Drawer: slide-out panel with title, type, summary, provenance, gap checklist, top 5 questions, actions | New | Clicking any node (map or inbox) opens drawer with full detail |
| Tue | Drawer actions: "Explore now" (sets next question), "Park", "Merge duplicate" (stub for P0) | New | Explore and Park work; Merge shows placeholder UI |
| Wed | Onboarding flow: project name + topic + optional audience inputs before first turn | New | First visit shows onboarding; data persists to session |
| Thu | Session context integration: pass onboarding data to LLM context assembly | New | Extraction and question prompts include project topic + audience |
| Fri | Integration testing: full user journey — onboard → chat → upload → inbox → detail drawer | — | All surfaces work together; no broken navigation or stale data |

**Week 9 exit criteria:** Node Detail Drawer shows full provenance, gaps, and questions for any node. Onboarding captures session context and feeds it to the LLM. All engagement surfaces are integrated.

---

## Bet 2 Milestone Checklist

- [ ] .txt and .docx upload works end-to-end (backend + frontend)
- [ ] Upload response shows "I found X ideas, Y stories" + top 3 nuggets
- [ ] Nuggets from uploads have document provenance (document_id + chunk)
- [ ] Nugget Inbox lists all session nuggets with sort/filter/search
- [ ] Nugget status (New/Explored/Parked) can be updated from inbox
- [ ] Node Detail Drawer shows provenance, gap checklist, and deep-dive questions
- [ ] "Explore now" from inbox or drawer sets the next question in chat
- [ ] Onboarding captures project name, topic, and audience
- [ ] Session context is used in LLM extraction and question prompts
- [ ] Full journey test passes: onboard → chat → upload → inbox → drawer
