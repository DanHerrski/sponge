# Sprint Plan: Bet 4 — User Validation & Iteration (Weeks 12–13)

**Goal:** Run 5 moderated user tests, fix critical issues, and produce a go/no-go recommendation.
**Capacity assumption:** 1 engineer + 1 product lead, 5 days per week.
**Prerequisite:** Bets 1–3 complete. Product is feature-complete for P0 scope.

---

## Week 12 — Test Preparation + First 3 Sessions

**Theme:** Prepare test materials, recruit participants, and run the first 3 user sessions.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | Prepare test materials: session script, debrief form, consent template, screen recording setup | PRD | Materials reviewed and ready; recording tools tested |
| Mon | Confirm 5 participants (recruited starting Week 10): schedule sessions across Tue–Thu | PRD | 5 confirmed with times; 2 backup candidates identified |
| Tue | **User Session 1:** 45-min moderated test (setup → chat → upload → review → debrief) | PRD | Session recorded; debrief notes captured; telemetry data logged |
| Wed | **User Session 2:** 45-min moderated test | PRD | Session recorded; debrief notes captured |
| Wed | Triage Session 1 findings: identify critical UX friction points | — | Top 3 friction points documented with severity |
| Thu | **User Session 3:** 45-min moderated test | PRD | Session recorded; debrief notes captured |
| Thu | Fix critical UX issues from Sessions 1–2 (if any) | — | Fixes deployed before Sessions 4–5 |
| Fri | Synthesize Sessions 1–3: pattern analysis, preliminary metric evaluation | — | Interim report: nugget quality, engagement, latency, friction points |

**Week 12 exit criteria:** 3 user sessions completed with recordings and data. Critical UX fixes from early sessions deployed. Preliminary patterns identified.

---

## Week 13 — Final Sessions + Evaluation + Roadmap

**Theme:** Complete testing, evaluate kill criteria, and make the go/no-go decision.

| Day | Task | Ref | Acceptance |
|-----|------|-----|------------|
| Mon | **User Session 4:** 45-min moderated test | PRD | Session recorded; debrief notes captured |
| Tue | **User Session 5:** 45-min moderated test | PRD | Session recorded; debrief notes captured |
| Wed | Full data synthesis: compile all 5 sessions — telemetry, debrief responses, observations | PRD | Data compiled in structured format; patterns documented |
| Wed | Calculate kill-threshold metrics across all 5 sessions | PRD | All 5 metrics evaluated with actual values vs. targets |
| Thu | Kill/pivot evaluation: write recommendation document | PRD | Clear go / no-go / pivot recommendation with supporting data |
| Thu | Identify top 3 user-requested features + top 3 friction points | PRD | Prioritized list from user feedback |
| Fri | Draft P1 roadmap (if go) or post-mortem (if no-go) | PRD | 1-page document reviewed with stakeholders |
| Fri | Present findings to stakeholders | PRD | Decision made and documented |

**Week 13 exit criteria:** All 5 user tests complete. Kill/pivot evaluation against all thresholds. Go/no-go recommendation delivered. P1 roadmap or post-mortem produced.

---

## Kill Threshold Evaluation Template

To be filled after all 5 sessions:

| Metric | Target | Session 1 | Session 2 | Session 3 | Session 4 | Session 5 | Median | Pass? |
|--------|--------|-----------|-----------|-----------|-----------|-----------|--------|-------|
| Time to first nugget | < 2 min | | | | | | | |
| Nuggets per 10-min | >= 5 | | | | | | | |
| Deep-dive engagement | >= 1 path | | | | | | | |
| Dup/generic rate | < 25% | | | | | | | |
| Session duration | 10–30 min | | | | | | | |

**Decision rule:** 0 kill thresholds triggered → Go. 1 threshold triggered → Conditional go with mitigation plan. 2+ triggered → Pause and product review.

---

## Bet 4 Milestone Checklist

- [ ] Test materials prepared (script, debrief form, consent, recording)
- [ ] 5 participants confirmed and scheduled
- [ ] Session 1 completed with recording + data
- [ ] Session 2 completed with recording + data
- [ ] Session 3 completed with recording + data
- [ ] Critical fixes from early sessions deployed
- [ ] Session 4 completed with recording + data
- [ ] Session 5 completed with recording + data
- [ ] Full data synthesis completed
- [ ] Kill thresholds evaluated with actual metrics
- [ ] Go/no-go recommendation written and presented
- [ ] P1 roadmap draft (or post-mortem) produced
- [ ] 4/5 users report session produced ideas they wouldn't have reached alone
