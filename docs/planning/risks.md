# Sponge MVP — Risk Register

Reference: [`mvp_spec.md`](../../mvp_spec.md) (P0 scope only)

---

## Risk Summary

| # | Risk | Type | Impact | Likelihood |
|---|------|------|--------|------------|
| 1 | Core value prop ("momentum") doesn't land | Product | Critical | Medium |
| 2 | Nugget extraction quality too low | Product/Tech | Critical | High |
| 3 | Next-best question feels irrelevant | Product | High | Medium |
| 4 | Mind map overwhelms rather than clarifies | Product | High | Medium |
| 5 | LLM latency breaks conversational flow | Technical | High | High |
| 6 | Deduplication is too aggressive or too permissive | Technical | High | High |
| 7 | Scoring lacks calibration — all nuggets score similarly | Technical | Medium | Medium |
| 8 | Context window limits hit as graph grows | Technical | High | Medium |
| 9 | Upload ingestion produces poor or noisy nuggets | Product/Tech | Medium | Medium |
| 10 | Data model changes force painful mid-MVP migrations | Technical | Medium | Low |

---

## Detailed Risk Analysis

### Risk 1 — Core value prop ("momentum") doesn't land

**Description:** After a 10–30 minute brain dump, the user does not feel organized momentum — the ranked mind map + deep-dive queue feels like noise, not progress.

- **Impact:** Critical — this is the entire MVP thesis (spec §0). If it fails, the product has no reason to exist.
- **Likelihood:** Medium — the loop design is sound, but perceived value is subjective and hard to predict.
- **Detection signal:** Users close the session early (<5 min), don't return, or describe the experience as "meh" in post-session feedback.
- **Mitigation:**
  - Run 3 moderated user tests before building full UI — use a Wizard-of-Oz prototype (manual nugget curation + scripted questions) to validate the loop feels valuable.
  - Ship a "session summary" at the end of each session so users see tangible output even if the graph is small.
- **Owner:** Product lead
- **Validation spike:** 5 moderated sessions with target users. Success = 4/5 say the session produced ideas they wouldn't have reached alone.

---

### Risk 2 — Nugget extraction quality too low

**Description:** The LLM extracts nuggets that are too generic, too granular, or miss the actual high-signal content the user provided (spec §6, §14.1).

- **Impact:** Critical — low-quality nuggets undermine trust in the system immediately. Users see "the AI doesn't get me."
- **Likelihood:** High — extraction from unstructured brain-dump text is an unsolved hard problem; first-pass prompts will need iteration.
- **Detection signal:** Duplicate/generic nugget rate > 25% in QA (spec §2), user ignores or dismisses surfaced nuggets.
- **Mitigation:**
  - Build an extraction eval harness early: 20 synthetic brain-dump transcripts, gold-standard nugget annotations, precision/recall metrics.
  - Use structured output (JSON schema) to constrain LLM extraction.
  - Iterate prompts against the eval set before integrating into the product.
- **Owner:** ML/LLM lead
- **Validation spike:** Extraction eval harness. Target: precision > 70%, recall > 60% on gold-standard set before shipping.

---

### Risk 3 — Next-best question feels irrelevant

**Description:** The system's "Next Best Question" (spec §7.3, §8) doesn't match what the user actually wants to explore — it feels like a non-sequitur or a generic interview question.

- **Impact:** High — the next-best question is the primary engagement driver. If it misfires, users disengage.
- **Likelihood:** Medium — the scoring dimensions (Impact, Leverage, Momentum, Connectivity, Gap criticality) are reasonable, but weighting them is tricky.
- **Detection signal:** Follow-through rate on suggested question < 30% (spec §13.3 telemetry), users consistently pick alternatives or skip.
- **Mitigation:**
  - Log every question shown vs. question answered. Use this data to re-weight scoring dimensions.
  - Include "Why this next" explanation (spec §7.3) so users understand the reasoning and can course-correct.
  - Allow easy skip/rephrase (spec §4.1 chat affordances).
- **Owner:** Product + ML/LLM lead
- **Validation spike:** A/B test 3 different scoring weight profiles on 10 synthetic sessions. Measure alignment with human-ranked "best next question."

---

### Risk 4 — Mind map overwhelms rather than clarifies

**Description:** The live-updating mind map (spec §4.1) shows too many nodes, poor layout, or confusing edges — users feel more lost than before.

- **Impact:** High — the mind map is a core differentiator. If it confuses users, it's worse than not having it.
- **Likelihood:** Medium — graph visualization is a well-known UX challenge, but the spec constrains to 5–20 nodes.
- **Detection signal:** Users don't interact with the mind map (no clicks on nodes), or explicitly say it's confusing.
- **Mitigation:**
  - Start with a simple force-directed layout, max 10 nodes visible by default.
  - Use progressive disclosure: show only nodes related to the current topic, expand on click.
  - Conduct 3 usability tests focused specifically on map readability.
- **Owner:** Frontend lead
- **Validation spike:** Clickable prototype (Figma or static React) with 3 user tests. Success = 4/5 users can identify their main ideas from the map.

---

### Risk 5 — LLM latency breaks conversational flow

**Description:** The core loop (spec §3) requires multiple LLM calls per turn (extract, score, generate questions, compose response). Total latency exceeds 5 seconds, breaking the "conversation" feel.

- **Impact:** High — the spec targets a "conversational, engaging" experience (spec §0). Multi-second pauses kill engagement.
- **Likelihood:** High — a single GPT-4-class call is 2–5s; chaining 3–4 calls easily exceeds 10s.
- **Detection signal:** Median turn latency > 5 seconds in telemetry. Users complain about speed.
- **Mitigation:**
  - Consolidate LLM calls: combine extraction + scoring + question generation into a single structured-output call where possible.
  - Stream the chat response while graph updates happen asynchronously in the background.
  - Use a faster model (GPT-4o-mini or Claude Haiku) for extraction; reserve the larger model for question generation.
  - Set a latency budget: 3s for chat response, 5s for graph update.
- **Owner:** Backend lead
- **Validation spike:** Benchmark the full pipeline on 10 sample inputs. Target: p50 < 3s for first token, p95 < 6s for complete response.

---

### Risk 6 — Deduplication is too aggressive or too permissive

**Description:** The embedding-based dedup (spec §6.3) either merges distinct ideas (losing nuance) or allows near-duplicates to clutter the graph.

- **Impact:** High — wrong dedup directly violates spec §14.2 and the <25% duplicate rate target (spec §2).
- **Likelihood:** High — similarity thresholds are notoriously hard to tune, especially on short text nuggets.
- **Detection signal:** Duplicate rate metric in telemetry. User complaints about "I already said that" (too permissive) or "where did my idea go?" (too aggressive).
- **Mitigation:**
  - Use a two-stage approach: embedding similarity for recall, then LLM confirmation for precision on close matches.
  - Expose a "merge" action in the UI (spec §4.3) so users can manually correct.
  - Tune thresholds on a labeled dataset of 50 nugget pairs (duplicate vs. distinct).
- **Owner:** ML/LLM lead
- **Validation spike:** Build a dedup eval set (50 pairs). Target: precision > 85%, recall > 75% at the chosen threshold.

---

### Risk 7 — Scoring lacks calibration — all nuggets score similarly

**Description:** The NuggetScore (spec §7.1) clusters around 50–70 for all nuggets, failing to differentiate high-signal from low-signal content.

- **Impact:** Medium — poor differentiation means the inbox ranking and next-best-question selection are effectively random.
- **Likelihood:** Medium — multi-dimensional scoring tends to average out unless dimensions are weighted with intention.
- **Detection signal:** Score distribution is unimodal with low variance (stdev < 10). Top-ranked nugget is not meaningfully better than 5th-ranked.
- **Mitigation:**
  - Anchor scoring with reference examples: provide the LLM with 3 gold-standard nuggets (score 90+) and 3 mediocre ones (score 30–) in the prompt.
  - Use per-dimension scores and only combine them with explicitly tuned weights.
  - Log score distributions and alert if variance drops below threshold.
- **Owner:** ML/LLM lead
- **Validation spike:** Score 30 synthetic nuggets (10 high / 10 mid / 10 low quality). Target: mean score of high > 75, mean score of low < 35.

---

### Risk 8 — Context window limits hit as graph grows

**Description:** The context assembly (spec §11) includes current input + top 10–20 nodes + session context + contradiction flags. After 20+ turns, this exceeds the LLM context window or degrades response quality.

- **Impact:** High — degraded context means the system forgets earlier ideas, asks redundant questions, or contradicts itself.
- **Likelihood:** Medium — modern models have 128k+ windows, but quality degrades with excessive context even within limits.
- **Detection signal:** Response quality drops noticeably after turn 15–20. System re-asks questions or misses connections to earlier content.
- **Mitigation:**
  - Use retrieval (vector search) to select only the most relevant nodes for each turn, not the most recent.
  - Maintain a compressed "session summary" that is updated every 5 turns (not full history).
  - Set a hard cap on context tokens (e.g., 8k for nodes, 2k for session summary) and measure quality at that budget.
- **Owner:** Backend + ML/LLM lead
- **Validation spike:** Simulate a 30-turn session. Measure whether the system references ideas from turns 1–5 accurately in turn 25+. Target: 80% recall of key early ideas.

---

### Risk 9 — Upload ingestion produces poor or noisy nuggets

**Description:** Uploaded documents (PDFs, transcripts, emails — spec §10) are parsed and chunked poorly, leading to low-quality or fragmented nuggets.

- **Impact:** Medium — uploads are a P0 use case (spec §1 use case #2), but users can fall back to chat-only if uploads fail.
- **Likelihood:** Medium — PDF parsing is unreliable; transcripts have no structure. Quality depends heavily on the parser.
- **Detection signal:** Users upload a doc but dismiss all surfaced nuggets. Post-upload engagement rate < 30%.
- **Mitigation:**
  - Start with plain text and DOCX only (most reliable parsing). Add PDF with a "best effort" disclaimer.
  - Use semantic chunking (paragraph/topic-based) rather than fixed-size token chunks.
  - Show the user "here's what I extracted" with an option to correct or retry.
- **Owner:** Backend lead
- **Validation spike:** Ingest 5 real-world documents (2 transcripts, 2 notes docs, 1 PDF). Target: at least 3/5 produce nuggets the author agrees are accurate.

---

### Risk 10 — Data model changes force painful mid-MVP migrations

**Description:** The data model (spec §5) needs significant changes after initial implementation — new node types, changed edge semantics, or schema additions — causing migration overhead.

- **Impact:** Medium — slows development but doesn't kill the product.
- **Likelihood:** Low — the spec is well-defined for P0; major schema changes are unlikely within P0 scope.
- **Detection signal:** More than 2 schema migrations needed before first user test.
- **Mitigation:**
  - Use a migration framework (Alembic for Python/SQLAlchemy) from day one.
  - Store flexible metadata as JSONB columns for node/nugget properties that might change.
  - Keep the schema close to spec §5 — resist adding fields "just in case."
- **Owner:** Backend lead
- **Validation spike:** Implement the schema, then attempt to add a hypothetical new node type and edge type. Confirm it requires < 1 hour of work including migration.

---

## Kill / Pivot Criteria

These criteria are tied directly to the MVP success metrics defined in [`mvp_spec.md` §2](../../mvp_spec.md):

| Metric | Target (spec §2) | Kill threshold | Action |
|--------|-------------------|----------------|--------|
| Time to first high-signal nugget | < 2 minutes | > 5 minutes after 3 prompt iterations | Kill current extraction approach; evaluate alternative models or manual curation |
| Nuggets per 10-min session | ≥ 5 (median) | < 2 (median) across 5 test sessions | Pivot: simplify to keyword/topic extraction instead of full nugget scoring |
| Deep-dive engagement | ≥ 1 path per session | 0 engagement across 5 test sessions | Pivot: replace proactive questions with on-demand "tell me more" UX |
| Duplicate/generic rate | < 25% | > 50% after tuning dedup | Kill graph-based dedup; fall back to simple title matching + manual merge |
| Session duration | 10–30 min target | Median < 3 min (users bail) | Kill: core value prop not landing; conduct user interviews before continuing |

**Decision process:** Evaluate kill criteria after the first 5 moderated user tests. If 2+ kill thresholds are hit simultaneously, pause development and conduct a product review before proceeding.
