# Sponge MVP Spec (P0 Only): Conversational Knowledge Graph + Next-Best Deep Dive

## 0. MVP Thesis

The MVP is not “write a book.”
The MVP is a system that helps a busy executive rapidly brain-dump ideas and materials while the product continuously:
A) detects high-signal “nuggets” worth content creation,
B) maps related paths to double-click into (knowledge graph / mind map),
C) prioritizes what to ask next (and why), in a conversational, engaging way.

Primary outcome: after 10–30 minutes, the user sees a coherent mind map + a ranked queue of high-value deep dives, and feels momentum.

---

## 1. Target Users & Primary Use Cases (P0)

### Target Users
- Busy executives / operators / founders who have expertise but limited writing time.

### P0 Use Cases
1) Brain dump in chat for 5–30 minutes; system extracts and prioritizes content-worthy ideas.
2) Upload resources (notes, emails, transcripts, docs); system synthesizes and surfaces strongest nuggets.
3) User follows “next best question” prompts to deepen the most valuable paths.
4) User can review and navigate their evolving mind map and nugget inbox.

Non-goals (P0)
- Full chapter drafting
- Full book exports
- Collaboration / sharing
- Scheduling, publishing workflows
- Voice transcription (can be designed for later)

---

## 2. Success Criteria (P0)

### User-perceived success (must)
- User feels the system “understands” their thinking and improves it.
- User is prompted with questions that are specific, insightful, and easy to answer.
- The mind map makes their ideas feel organized and expandable.

### Measurable success (P0)
- Time to first “high-signal nugget surfaced”: < 2 minutes from first input
- At least 5 nuggets extracted from a 10-minute brain dump (median)
- User engages with at least 1 deep-dive path per session (median)
- Duplicate/generic nugget rate < 25% (internal QA rubric)

---

## 3. Core Product Loop (P0)

Every time the user:
- sends a chat message, OR
- uploads a resource

The system runs:

1) Ingest input
2) Extract candidate nuggets + entities + claims + stories + frameworks
3) Score each nugget (content-worthiness)
4) Link nuggets into the Knowledge Graph (nodes + edges)
5) Identify gaps required to make each nugget “publishable”
6) Decide Next-Best Deep Dive (1 primary + 2 alternates)
7) Update UI (mind map, nugget inbox, next question card)

---

## 4. UX Surfaces (P0)

### 4.1 Main Screen: Chat + Mind Map + Next Question
Layout:
- Left: Chat
- Right: Mind Map pane (live updating)
- Bottom/Side card: “Next Best Question” (primary) + “Other paths” (2 alternates)

P0 Chat affordances:
- Buttons: Pause, Skip, Rephrase, Summarize
- Answer modes: Quick bullets, Tell a story, Give steps, I’m not sure, Skip

P0 Mind Map behavior:
- Shows 5–20 most relevant nodes (not entire graph) with zoom/expand
- Nodes are clickable to open details drawer (see 4.3)
- Visual distinction by node type (Idea/Story/Framework/Definition/Evidence) via icon or label

P0 Next Question card:
- Displays 1 primary question (timeboxed suggestion: 60 seconds)
- Shows “Why this next” in one sentence
- Shows 2 alternative paths the user can select instead

### 4.2 Nugget Inbox (List)
A separate view or tab that lists extracted nuggets, ranked by score.
Each nugget row shows:
- Title (auto-generated)
- Type (Idea/Story/Framework)
- NuggetScore (0–100)
- Status: New / Explored / Parked
- Button: Double-click (opens deep-dive paths)

Sorting/filtering (P0):
- Sort by score
- Filter by type
- Search by keyword

### 4.3 Node Detail Drawer (from Mind Map or Nugget Inbox)
Shows:
- Node title + type
- 1–3 sentence summary
- Provenance (which chat turns / which uploaded docs)
- “What’s missing” checklist (gaps)
- Recommended deep-dive questions (top 5)
- Actions: Explore now (sets next question), Park, Merge duplicate

---

## 5. Knowledge Graph & Data Model (P0)

### 5.1 Node Types (P0)
- Idea: a claim/insight/opinion
- Story: anecdote with context, tension, outcome, lesson
- Framework: steps, heuristic, checklist, model
- Definition: term + meaning in the user’s language
- Evidence: metric, concrete example, citation-like support
- Theme: higher-level grouping label (auto-generated)

Note: Content Asset nodes (posts/chapters) are out of scope for P0.

### 5.2 Edge Types (P0)
- supports (Evidence/Story/Idea -> Idea/Framework)
- example_of (Story/Evidence -> Idea/Framework)
- expands_on (Idea/Framework -> Idea/Framework)
- related_to (any <-> any)
- contradicts (Idea <-> Idea) (flagging only, not “resolving”)

### 5.3 Nugget Object (P0)
A Nugget is a wrapper around a high-value node plus prioritization metadata:
- nugget_id
- node_id
- nugget_type (Idea/Story/Framework)
- title
- short_summary
- NuggetScore (0–100)
- missing_fields (list)
- suggested_formats (optional label only: post/chapter/talk; no generation in P0)
- next_questions (ranked list)

### 5.4 Provenance (P0)
All nodes must store:
- source_type: chat | upload
- source_id: chat_turn_id or document_id + chunk_id
- timestamp
- confidence (low/med/high)

---

## 6. Nugget Extraction (P0)

### 6.1 Inputs
- Chat message text
- Uploaded doc chunks (notes, emails, transcripts, PDFs/DOCX/Google Doc export)

### 6.2 Output (structured)
From each input, the system extracts:
- candidate_nodes: list of nodes (type, title, summary, key phrases)
- entities: people/orgs/products/industries (optional but helpful)
- claims: explicit/implicit assertions
- stories: narrative segments
- frameworks: stepwise patterns
- definitions: terms that appear “special” in the user’s language

### 6.3 De-duplication (P0)
Before creating a new node:
- Attempt to match to existing nodes via embedding similarity + title similarity
- If similarity above threshold:
  - merge or link as expands_on
- Must prevent “same idea repeated 5 times” clutter

---

## 7. Scoring & Prioritization (P0)

### 7.1 NuggetScore (Content-worthiness) (0–100)
Compute NuggetScore using a hybrid approach:
- Heuristic signals (fast, deterministic)
- Optional LLM rubric scoring (bounded, consistent schema)

Required scoring dimensions (P0):
- Specificity: concrete details, constraints, names, numbers
- Novelty: not generic advice; distinct viewpoint or experience
- Authority: indicates lived experience / credibility (specific roles, situations)
- Actionability: implies steps, decisions, heuristics, repeatability
- Story energy (for Story nuggets): stakes, conflict, outcome, lesson
- Audience resonance: clear “who this helps” implied

Minimum requirement:
- Each nugget must store per-dimension scores + total.

### 7.2 Gap Detection (“What’s missing”) (P0)
For each nugget, identify missing fields that would strengthen it:
- Example missing
- Evidence missing
- Steps missing
- Counterpoint missing
- Definition missing
- Audience missing
- Outcome/lesson missing (for stories)

Store missing_fields as a checklist.

### 7.3 NextBestDiveScore (Choose what to ask next)
For each candidate deep-dive path, compute:
- Impact: will this unlock stronger content or clearer thinking?
- Leverage: reusable across multiple nuggets/themes?
- Momentum: likely easy for user to answer quickly?
- Connectivity: strengthens links/coherence in the graph?
- Gap criticality: does it fill a key missing field?

Output:
- Primary next question (1)
- Alternative paths (2)

System must produce “Why this next”:
- single sentence referencing impact + momentum (no jargon)

---

## 8. Deep-Dive Question Generation (P0)

For each high-scoring nugget, generate question paths in 5 buckets:

1) Clarify the claim
- What do you mean by X?
- What’s the precise statement?

2) Prove it (evidence/examples)
- What’s a concrete example?
- What metric changed, or what outcome occurred?

3) Operationalize it (steps/checklist)
- If someone did this tomorrow, what are the steps?
- What are the do’s and don’ts?

4) Differentiate it (contrast/counterpoint)
- What’s the common wrong advice here?
- Where does this break down?

5) Package it (audience/promise)
- Who is this most useful for?
- What pain does it solve?

Requirements (P0):
- Each question must be specific to the nugget (no generic templates)
- Each question must be answerable in under 2 minutes
- Provide a timebox suggestion per question: 30s / 2m / deep

---

## 9. Conversational Behavior Contract (P0)

After each user input, the assistant response must follow this structure:

A) Captured Nuggets (2–4 bullets)
- Each bullet is clickable (opens node drawer)

B) Mind Map Updated (short)
- One sentence describing what changed (ex: “Added a new framework linked to your ‘sourcing signal’ idea.”)

C) Next Best Question (only 1)
- The single question
- Show suggested answer mode buttons: Quick bullets / Tell story / Give steps

D) Why This Next (1 sentence)

E) Two Alternative Paths
- Provide two other questions, each labeled with the nugget it belongs to

Hard constraints:
- Do not ask multiple primary questions at once
- Keep the main prompt short and high-signal
- Maintain a friendly, energetic tone appropriate for execs (crisp, not verbose)

---

## 10. Resource Upload Ingestion (P0)

### 10.1 Supported Upload Types (P0)
- Plain text
- PDF
- DOCX
- Copy-pasted email/text
- Transcript text (manual paste)

### 10.2 Ingestion Pipeline (P0)
1) Parse text
2) Chunk into semantically coherent units
3) Embed chunks for retrieval/dedup
4) Extract nuggets from chunks
5) Attach provenance (doc + chunk)
6) Summarize “What I found” and propose next-best deep dive

### 10.3 Post-upload UX (P0)
Assistant says:
- “I found X strong ideas and Y supporting stories.”
- Shows top 3 nuggets
- Asks: “Want to deep dive one now?” + presents 3 choices

---

## 11. Retrieval & Context (P0)

The assistant must be able to:
- Retrieve top relevant nodes for the current conversation turn
- Retrieve supporting provenance snippets for a node
- Avoid contradiction by referencing existing nodes when drafting questions

Context assembly for each assistant response (P0):
- Current user input
- Top N relevant nodes (N=10–20)
- Book-level “Session Context” (see below)
- Any contradictions flags relevant to the current topic

Session Context (P0):
- user’s stated topic (if any)
- intended audience (if captured)
- preferred tone (optional)
If unknown, system must infer lightly but not assume strongly.

---

## 12. Minimal Onboarding (P0)

P0 onboarding is lightweight:
- Project name
- Topic (freeform)
- Optional: audience (freeform)
- Optional: style inspirations (names or upload sample writing)
- Prompt: “Drop anything you already have: notes, emails, transcripts.”

No heavy wizard required for P0.

---

## 13. Storage & Backend Requirements (P0)

### 13.1 Storage
- Nodes table
- Edges table
- Nuggets table
- Sources table (documents + chunks)
- Chat turns table
- Embeddings index (vector store)

### 13.2 APIs (P0)
- POST /chat_turn (ingest user message; returns structured assistant response + graph updates)
- POST /upload (ingest doc; returns nugget extraction summary + next-best choices)
- GET /graph_view (returns nodes/edges for mind map pane)
- GET /node/:id (returns node detail + provenance + questions)
- POST /node/:id/merge (merge duplicates)
- POST /nugget/:id/status (New/Explored/Parked)

### 13.3 Observability (P0)
Log per turn:
- extracted nugget count
- average NuggetScore
- selected next question
- user response length
- follow-through rate on suggested question

---

## 14. Guardrails (P0)

### 14.1 Anti-generic filter
If a nugget is generic:
- mark as low novelty
- do not surface it in top nuggets unless it links strongly to a unique story/framework

### 14.2 Duplication control
- enforce dedup thresholds
- prefer linking/expanding over new nodes

### 14.3 Contradiction flagging (soft)
- If two ideas conflict, flag “possible contradiction”
- Ask user a clarifying question only when it becomes relevant

### 14.4 Safety & privacy (baseline)
- User uploads are private to their account
- Allow delete project (P0 if easy; otherwise queued for P1)
- Do not train on user content (must be stated in product policy, implementation dependent)

---

## 15. Acceptance Criteria (P0)

### Conversational loop
- Given a user message, system surfaces 2–4 nuggets, updates mind map, asks 1 next-best question, and provides 2 alternate paths.
- Next-best question is specific to at least one extracted nugget and references its missing gap type (example/steps/proof/etc.).

### Knowledge graph
- Given 10 chat turns, system creates a graph with:
  - at least 5 nodes
  - at least 4 edges
  - provenance stored for each node
- Mind map pane loads a coherent subset (5–20 nodes) relevant to current discussion.

### Upload ingestion
- Given an uploaded transcript, system extracts nuggets with provenance and offers top 3 deep-dive options in chat.

### Scoring
- Every surfaced nugget includes:
  - total NuggetScore
  - per-dimension scores
  - missing_fields checklist

### Deduplication
- Repeating the same idea in multiple turns does not create >2 duplicate nodes; instead it links as expands_on or merges.

---

## 16. Out of Scope (Explicitly Not P0)

- Full book outline editor
- Chapter drafting and export
- Multi-user collaboration
- Scheduling/content calendar
- Voice recording/transcription
- Fine-grained style mimicry enforcement (keep lightweight)
- Publishing pipeline integrations

---

## 17. MVP Deliverable Summary (P0 Checklist)

Must ship:
- Chat-based brain dump experience
- Live mind map / knowledge graph view
- Nugget extraction + scoring + dedup
- Deep-dive path generation
- Next-best question prioritization with “why”
- Nugget inbox + node detail drawer + provenance
- Resource upload ingestion with nugget surfacing
- Minimal onboarding and session context
- Basic telemetry and guardrails

End of Sponge MVP Spec (P0 Only)
