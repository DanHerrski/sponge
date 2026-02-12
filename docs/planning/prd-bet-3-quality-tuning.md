# PRD-lite: Bet 3 — Quality, Tuning & Guardrails

**Timeframe:** Weeks 10–11 | **Effort:** ~10 dev-days | **Owner:** Eng Lead + ML/LLM Lead
**Epics:** 10 (Observability + Guardrails) + scoring calibration + dedup tuning + chat affordances

---

## Problem Statement

Without calibrated scoring, tuned deduplication, and anti-generic filtering, the system will produce noisy, undifferentiated output that erodes user trust. Without telemetry, we have no visibility into system behavior or ability to iterate on quality. These are prerequisites for meaningful user validation in Bet 4.

## Objective

Calibrate scoring to produce clear signal differentiation, tune dedup thresholds on labeled data, add anti-generic filtering, implement structured telemetry for every turn, and add chat affordance buttons for user control.

## Success Criteria

| Metric | Target |
|--------|--------|
| Score differentiation | High-quality nuggets mean > 75, low-quality mean < 35 |
| Score variance | Stdev > 15 across a session's nuggets |
| Duplicate rate | < 25% of turns trigger dedup |
| Anti-generic filter | Low-novelty nuggets (Novelty < 20) demoted from top results |
| Telemetry coverage | Every `POST /chat_turn` produces a structured log entry |
| Follow-through tracking | System logs suggested question vs. user's actual next message |
| Chat affordances | Pause, Skip, Rephrase buttons functional in chat UI |

## Components

### Observability (Epic 10)

| Component | Description | Size |
|-----------|-------------|------|
| Structured logging middleware | Log per-turn: nugget count, avg score, selected question, latency | 1d |
| Duplication rate metric | Track dedup triggers per session, log rate | 0.5d |
| Follow-through tracking | Compare suggested question with user's next message | 1d |
| Soft contradiction detection | Embedding similarity + opposing sentiment → flag as `contradicts` edge | 1d |

### Scoring Calibration

| Component | Description | Size |
|-----------|-------------|------|
| Anchor examples in prompt | Add 3 high-scoring (90+) and 3 low-scoring (30-) reference nuggets to extraction prompt | 0.5d |
| Per-dimension weight tuning | Evaluate dimension weights on 30 synthetic nuggets (10 high/10 mid/10 low) | 1d |
| Score distribution monitoring | Alert if score variance drops below threshold | 0.5d |

### Dedup Tuning

| Component | Description | Size |
|-----------|-------------|------|
| Labeled dedup eval set | Create 50 nugget pairs (duplicate vs. distinct) with gold labels | 1d |
| Threshold optimization | Sweep cosine similarity thresholds, measure precision/recall on eval set | 0.5d |
| LLM confirmation stage | For close matches (similarity 0.80–0.92), add lightweight LLM yes/no call | 0.5d |

### Chat Affordances

| Component | Description | Size |
|-----------|-------------|------|
| Affordance buttons | Pause, Skip, Rephrase, Summarize buttons in chat UI | 1d |
| Anti-generic filter | Check Novelty dimension; demote low-scoring nuggets from top results | 0.5d |

## Technical Notes

- **Structured logging:** Use Python `structlog` with JSON output. Log fields: `session_id`, `turn_id`, `nugget_count`, `avg_score`, `max_score`, `min_score`, `selected_question`, `latency_ms`, `dedup_triggered`, `model_used`.
- **Follow-through:** Compute cosine similarity between the suggested question's embedding and the user's next message embedding. Similarity > 0.6 = "followed through."
- **Contradiction detection:** Soft flag only. Detect pairs of nodes with high embedding similarity but opposing sentiment signals (e.g., "always do X" vs. "never do X"). Create `contradicts` edge but do not surface in UI for P0.
- **Scoring anchors:** Embed reference nuggets directly in the extraction prompt's system message as calibration examples.

## Risks (Bet 3-specific)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scoring anchors bias extraction | Medium | Test on held-out inputs; ensure anchors are domain-neutral |
| Dedup eval set too small | Medium | Start with 50 pairs; expand if precision/recall are unstable |
| Follow-through metric is noisy | Low | Use as directional signal, not absolute metric |

## Out of Scope (Bet 3)

- Automated A/B testing framework
- User-facing analytics dashboard
- Advanced contradiction resolution (beyond flagging)
- Model fine-tuning

## Definition of Done

Scoring produces clear differentiation on synthetic data (high > 75, low < 35). Dedup precision > 85% on labeled eval set. Every chat turn produces a structured log entry with all required fields. Anti-generic filter suppresses low-novelty nuggets. Chat UI includes functional Pause, Skip, and Rephrase buttons.
