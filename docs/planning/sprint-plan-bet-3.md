# Sprint Plan: Bet 3 — Quality, Tuning & Guardrails (Weeks 10–11)

**Goal:** Calibrate scoring, tune dedup, add observability, and implement chat affordances.
**Capacity assumption:** 1 full-stack engineer, 5 dev-days per week.
**Prerequisite:** Bets 1–2 complete. All surfaces functional.

---

## Week 10 — Observability + Scoring Calibration

**Theme:** Instrument the system for visibility and ensure scores actually differentiate nugget quality.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | 10.1 Structured logging middleware: log per-turn metrics (nugget count, avg/max/min score, selected question, latency) | E10 | Every `POST /chat_turn` produces a JSON log entry with all fields |
| Tue | 10.3 Duplication rate metric: track dedup triggers per session, log rate | E10 | Dup rate logged per session; queryable from logs |
| Tue | Score distribution monitoring: log score variance, alert if stdev < 10 | New | Warning emitted if scores cluster |
| Wed | Scoring anchor examples: add 3 high-scoring (90+) and 3 low-scoring (30-) reference nuggets to extraction prompt | New | Prompt includes calibration examples |
| Thu | Per-dimension weight tuning: evaluate on 30 synthetic nuggets (10 high/10 mid/10 low) | New | High mean > 75, low mean < 35, stdev > 15 |
| Fri | 10.5 Follow-through tracking: compare suggested question with user's next message (embedding similarity) | E10 | Follow-through logged per turn; similarity > 0.6 = "followed" |

**Week 10 exit criteria:** Every turn produces structured telemetry. Scoring produces clear differentiation on synthetic test data. Follow-through tracking is operational.

---

## Week 11 — Dedup Tuning + Guardrails + Chat Affordances

**Theme:** Tune dedup precision, add quality filters, and give users control over the conversation.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | Create labeled dedup eval set: 50 nugget pairs (duplicate vs. distinct) with gold labels | New | Eval set committed to repo; covers edge cases (similar vocab + different ideas) |
| Mon | Threshold optimization: sweep cosine thresholds (0.75–0.95), measure precision/recall | New | Chosen threshold achieves precision > 85%, recall > 75% |
| Tue | LLM confirmation for close matches: similarity 0.80–0.92 triggers lightweight yes/no LLM call | New | Close matches get LLM check; clear matches/misses skip it |
| Wed | 10.2 Anti-generic filter: check Novelty dimension, demote nuggets with Novelty < 20 | E10 | Low-novelty nuggets excluded from top captured_nuggets in response |
| Wed | 10.4 Soft contradiction detection: high embedding similarity + opposing sentiment → `contradicts` edge | E10 | Contradicting nodes flagged with edge type; not surfaced in UI |
| Thu | Chat affordance buttons: Pause, Skip, Rephrase, Summarize | New | Buttons render in chat; each triggers appropriate behavior |
| Thu | Pause: temporarily stops proactive questions | New | Paused state persists; questions resume on unpause |
| Fri | Skip: dismisses current question, shows next alternate | New | Current question dismissed; next alternate promoted |
| Fri | Rephrase: regenerates current question with different wording | New | Same target nugget/gap, new phrasing |

**Week 11 exit criteria:** Dedup precision > 85% on labeled eval set. Anti-generic filter suppresses low-novelty nuggets. Chat affordances (Pause, Skip, Rephrase) are functional. Soft contradiction detection creates `contradicts` edges.

---

## Bet 3 Milestone Checklist

- [ ] Every `POST /chat_turn` produces a structured log entry (JSON)
- [ ] Log fields include: nugget_count, avg_score, max_score, min_score, latency_ms, dedup_triggered, selected_question
- [ ] Duplication rate tracked and logged per session
- [ ] Follow-through rate tracked (suggested question vs. user's next message)
- [ ] Score distribution: high-quality nuggets mean > 75, low-quality mean < 35
- [ ] Score variance: stdev > 15 across session nuggets
- [ ] Dedup precision > 85%, recall > 75% on 50-pair eval set
- [ ] LLM confirmation fires for close cosine matches (0.80–0.92)
- [ ] Anti-generic filter demotes nuggets with Novelty < 20
- [ ] Soft contradiction detection creates `contradicts` edges
- [ ] Pause, Skip, Rephrase buttons functional in chat UI
