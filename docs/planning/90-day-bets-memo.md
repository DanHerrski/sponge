# Sponge — 90-Day Bets Memo

**Product:** Sponge — Conversational Knowledge Graph for Executive Brain Dumps
**Owner:** Product Lead | **Eng Lead:** TBD | **Date:** 2026-02-12
**Thesis:** After 10-30 minutes of brain-dumping, a busy executive sees a coherent mind map + ranked queue of high-value deep dives and feels momentum.

---

## The 4 Bets

### Bet 1 — Steel Thread: Core Value Loop (Weeks 1–6)

**Hypothesis:** If we wire chat input → nugget extraction → scoring → dedup → graph write → next-best question → UI render end-to-end, we can prove the core product loop delivers momentum in a single session.

**Key result:** A user types 3+ messages and sees extracted nuggets, a live mind map with 3+ nodes and 2+ edges, and a targeted next-best question — all in under 8 seconds per turn.

**Scope:** Epics 1–8 (scaffolding, data model, chat ingestion, extraction + scoring, dedup, graph write, next-best question, steel-thread UI). 28 tasks, ~28.5 dev-days.

**Top risk:** Nugget extraction quality too low (Risk 2). Mitigated by eval harness with 20 synthetic transcripts before shipping.

---

### Bet 2 — Content Ingestion & Engagement Surfaces (Weeks 7–9)

**Hypothesis:** Executives will dump existing materials (notes, transcripts, docs) if the system can ingest them and surface nuggets at the same quality as chat — and they need an inbox to manage what the system finds.

**Key result:** A user uploads a 3-page doc and sees 3+ extracted nuggets with provenance, browsable in a Nugget Inbox with sort/filter. Node Detail Drawer shows gap checklists and deep-dive questions.

**Scope:** Epic 9 (upload ingestion) + Nugget Inbox + Node Detail Drawer + lightweight onboarding. ~15 dev-days.

**Top risk:** Upload parsing produces noisy nuggets (Risk 9). Mitigated by starting with .txt/.docx only, semantic chunking, and user-visible "here's what I found" confirmation.

---

### Bet 3 — Quality, Tuning & Guardrails (Weeks 10–11)

**Hypothesis:** Without calibrated scoring, dedup tuning, and anti-generic filtering, the system will feel noisy and untrustworthy — these are table stakes for an "intelligent" product.

**Key result:** Score distribution shows clear separation (high > 75, low < 35). Duplicate rate < 25%. Anti-generic filter suppresses low-novelty nuggets. Structured telemetry logs every turn.

**Scope:** Epic 10 (observability + guardrails) + scoring calibration + dedup threshold tuning + chat affordances (Pause, Skip, Rephrase). ~10 dev-days.

**Top risk:** Scoring clusters around 50-70, failing to differentiate (Risk 7). Mitigated by anchor examples in prompts and per-dimension weight tuning.

---

### Bet 4 — User Validation & Iteration (Weeks 12–13)

**Hypothesis:** The only way to know if "momentum" lands is to put the product in front of 5 target users and measure whether they engage, return, and articulate value.

**Key result:** 5 moderated user tests completed. 4/5 users say the session produced ideas they wouldn't have reached alone. 0 kill thresholds triggered. Confident go/no-go decision for P1.

**Scope:** 5 moderated test sessions, critical UX fixes from test feedback, kill/pivot evaluation against defined thresholds, P1 roadmap draft.

**Top risk:** Core value prop doesn't land (Risk 1). If 2+ kill thresholds are hit simultaneously, pause development and conduct product review.

---

## Kill Thresholds (evaluated at Week 13)

| Metric | Target | Kill if... |
|--------|--------|------------|
| Time to first nugget | < 2 min | > 5 min after 3 prompt iterations |
| Nuggets per 10-min session | >= 5 | < 2 across 5 test sessions |
| Deep-dive engagement | >= 1 path/session | 0 engagement across 5 sessions |
| Duplicate/generic rate | < 25% | > 50% after tuning |
| Session duration | 10-30 min | Median < 3 min |

## Resource Assumptions

- 1 full-stack engineer + 1 LLM/ML engineer (shared or overlapping)
- LLM API budget: ~$200/month (OpenAI GPT-4o-mini for extraction, GPT-4o for questions)
- Infrastructure: Supabase (Postgres + pgvector) + Vercel (frontend)
- No dedicated design resource — use component libraries + rapid prototyping

## Dependencies & Sequencing

```
Bet 1 (Weeks 1-6) ──sequential──▶ Bet 2 (Weeks 7-9)
                                         │
                                    Bet 3 (Weeks 10-11) ◀── can partially overlap
                                         │
                                    Bet 4 (Weeks 12-13)
```

Bets 2 and 3 have light overlap potential (observability can start in Week 9 while upload polish finishes). Bet 4 is strictly serial — requires a working product.
