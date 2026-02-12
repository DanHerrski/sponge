# PRD-lite: Bet 4 — User Validation & Iteration

**Timeframe:** Weeks 12–13 | **Effort:** ~10 dev-days | **Owner:** Product Lead + Eng Lead
**Scope:** Moderated user tests, critical fixes, kill/pivot evaluation, P1 roadmap

---

## Problem Statement

The product thesis — that executives feel "momentum" after brain-dumping into Sponge — is untested with real users. All upstream bets have optimized for technical completeness, but the only meaningful validation is putting the product in front of target users and measuring their response. This bet is the gate to P1 investment.

## Objective

Conduct 5 moderated user test sessions with target users (busy executives/founders/operators). Evaluate results against kill thresholds. Fix critical UX issues. Produce a confident go/no-go recommendation for P1 with a draft roadmap.

## Success Criteria

| Metric | Target |
|--------|--------|
| User tests completed | 5 moderated sessions |
| Core value validation | 4/5 users say session produced ideas they wouldn't have reached alone |
| Time to first nugget | < 2 min (median across 5 sessions) |
| Session duration | 10–30 min (median) |
| Deep-dive engagement | >= 1 path followed per session (median) |
| Kill thresholds triggered | 0 (see kill criteria below) |
| Critical UX fixes | Shipped within 48 hours of identification |
| P1 roadmap | Draft produced and reviewed |

## Test Protocol

### Participant Criteria
- Busy executive, operator, or founder
- Has expertise in a domain they could talk about for 30 minutes
- Has some existing materials (notes, docs) they could upload
- Not involved in building Sponge

### Session Structure (45 min each)

| Phase | Duration | Activity |
|-------|----------|----------|
| Setup | 5 min | Brief intro, set project name/topic via onboarding |
| Free chat | 15 min | Brain-dump on their topic — no guidance beyond "share what you know" |
| Upload test | 5 min | Upload a real document, review extracted nuggets |
| Guided review | 10 min | Walk through mind map, inbox, node details — think-aloud |
| Debrief | 10 min | Structured questions (see below) |

### Debrief Questions
1. Did the system capture your most important ideas? Which ones did it miss?
2. Were the questions it asked useful? Did any feel irrelevant or generic?
3. Does the mind map make your ideas feel more organized?
4. Would you come back tomorrow to continue this session? Why or why not?
5. On a scale of 1–5: "This session helped me think more clearly about my topic."

### Data Collection
- Screen recording of entire session
- Structured log data from telemetry (nugget counts, scores, latency, follow-through)
- Debrief responses (written notes)
- Researcher observations (friction points, confusion, delight moments)

## Kill / Pivot Evaluation

Evaluated after all 5 sessions are complete:

| Metric | Target | Kill if... | Action |
|--------|--------|------------|--------|
| Time to first nugget | < 2 min | > 5 min after 3 prompt iterations | Kill extraction approach |
| Nuggets per 10-min session | >= 5 | < 2 median | Pivot to keyword extraction |
| Deep-dive engagement | >= 1 path/session | 0 across 5 sessions | Pivot to on-demand "tell me more" |
| Duplicate/generic rate | < 25% | > 50% after tuning | Fall back to title matching + manual merge |
| Session duration | 10–30 min | Median < 3 min | Kill — conduct user interviews |

**Decision rule:** If 2+ kill thresholds are hit simultaneously, pause all development. Conduct a product review with stakeholders before any further investment.

## Iteration Scope (Weeks 12–13)

### Critical fixes only
- UX friction points identified in first 2 sessions (fix before sessions 3–5)
- Extraction prompt adjustments if nugget quality is consistently low
- Mind map layout issues if users can't parse the visualization
- Latency improvements if turn time consistently exceeds 8 seconds

### Not in scope for iteration
- New features
- Architecture changes
- Re-platforming
- Major UI redesigns

## P1 Roadmap Draft (output of this bet)

If go: produce a 1-page P1 roadmap covering:
- Top 3 user-requested features from test sessions
- Technical debt items identified during P0
- Scaling considerations (multi-user, auth, persistence)
- Content generation capabilities (chapter drafting, export)
- Estimated P1 timeline and resource needs

If no-go: produce a post-mortem documenting:
- Which hypotheses failed and why
- What telemetry data showed
- Whether a pivot is viable or the concept should be shelved

## Components

| Component | Description | Size |
|-----------|-------------|------|
| Test protocol & materials | Session script, debrief form, consent template | 1d |
| Participant recruitment | Identify and schedule 5 target users | 1d |
| Session facilitation | Conduct 5 moderated sessions (not all in same day) | 3d |
| Data synthesis | Compile recordings, logs, debrief responses; identify patterns | 1.5d |
| Critical UX fixes | Address top 3–5 friction points from early sessions | 2d |
| Kill/pivot evaluation | Evaluate metrics against thresholds; write recommendation | 0.5d |
| P1 roadmap draft | Produce 1-page roadmap or post-mortem | 1d |

## Risks (Bet 4-specific)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Can't recruit 5 target users in time | High | Start recruiting in Week 10; have 8 candidates lined up |
| Users test with trivial topics | Medium | Pre-screen for domain expertise; suggest topics in advance |
| Confirmation bias in test facilitation | Medium | Use structured debrief; have second observer; record sessions |
| Critical fixes destabilize the product | Medium | Only fix clear UX friction; no architectural changes |

## Definition of Done

5 user tests completed with documented results. Kill/pivot evaluation completed against all thresholds. Either: (a) confident go recommendation with P1 roadmap draft, or (b) documented no-go with post-mortem and pivot options. Critical UX fixes from testing are shipped.
