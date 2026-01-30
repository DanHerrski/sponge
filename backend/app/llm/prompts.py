"""Versioned prompts for the Sponge extraction pipeline.

Each prompt is versioned (v1, v2, etc.) to track changes over time.
Prompts are designed to:
- Avoid generic advice
- Prefer concrete experience
- Output strictly to defined JSON schemas
"""

# --- Extraction Prompt v1 ---

EXTRACT_NUGGETS_V1 = """You are extracting high-signal knowledge nuggets from a brain-dump conversation.

Your task is to identify 2-6 distinct nuggets from the user's message. Each nugget should be:
- SPECIFIC: Based on real experience, not generic advice
- CONCRETE: Contains details, names, numbers, or specific situations
- VALUABLE: Something that could become compelling content

Nugget types:
- "idea": A distinct insight, principle, or observation
- "story": A narrative with characters, conflict, and resolution
- "framework": A mental model, process, or structured approach

CRITICAL RULES:
1. NEVER extract generic advice like "communication is important" or "be a good leader"
2. PREFER nuggets with specific examples, names, metrics, or time references
3. Each nugget must be DISTINCT - don't create overlapping nuggets
4. If the input is too vague, extract fewer nuggets with lower confidence
5. Use the user's actual language in key_phrases

CONFIDENCE LEVELS:
- "high": Clear, specific, experience-based insight
- "medium": Good insight but could use more detail
- "low": Vague or potentially generic

User message:
{user_message}

Session context (previous high-value nuggets):
{session_context}

Output your response as valid JSON matching this schema:
{{
  "nuggets": [
    {{
      "nugget_type": "idea" | "story" | "framework",
      "title": "Concise title (5-100 chars)",
      "summary": "2-3 sentence summary (20-500 chars)",
      "key_phrases": ["phrase1", "phrase2"],
      "confidence": "high" | "medium" | "low"
    }}
  ],
  "extraction_notes": "Optional notes about extraction quality"
}}
"""

# --- Scoring Prompt v1 ---

SCORE_NUGGETS_V1 = """You are scoring knowledge nuggets for content potential.

Score each nugget across 6 dimensions (0-100 each):

1. SPECIFICITY (0-100): How specific vs generic?
   - 90+: Names, numbers, exact dates, specific situations
   - 60-89: Clear context but missing some details
   - 30-59: General patterns without specifics
   - 0-29: Generic advice anyone could give

2. NOVELTY (0-100): How fresh/unexpected?
   - 90+: Counterintuitive or rarely discussed
   - 60-89: Fresh take on known topic
   - 30-59: Common knowledge with personal spin
   - 0-29: Cliche or obvious

3. AUTHORITY (0-100): Real experience backing it?
   - 90+: Clear first-hand experience with outcomes
   - 60-89: Experience mentioned but outcomes unclear
   - 30-59: Sounds like experience but not explicit
   - 0-29: Could be theoretical or borrowed

4. ACTIONABILITY (0-100): Can someone act on this?
   - 90+: Clear steps someone could take today
   - 60-89: Direction clear, details need work
   - 30-59: Interesting but hard to apply
   - 0-29: Philosophical, no clear action

5. STORY_ENERGY (0-100): Narrative power?
   - 90+: Compelling characters, tension, resolution
   - 60-89: Good anecdote, needs polish
   - 30-59: Facts without narrative arc
   - 0-29: Dry or abstract

6. AUDIENCE_RESONANCE (0-100): Will target audience care?
   - 90+: Addresses pain points directly
   - 60-89: Relevant but not urgent
   - 30-59: Interesting but niche
   - 0-29: Unclear who benefits

Also identify 1-3 MISSING_FIELDS that would strengthen each nugget:
- "example": Needs a concrete example
- "evidence": Needs data or proof
- "steps": Needs actionable steps
- "counterpoint": Needs to address objections
- "definition": Needs clearer definition
- "audience": Needs clearer target audience
- "outcome": Needs to show results

Nuggets to score:
{nuggets_json}

Session context:
{session_context}

Previously downvoted nuggets (penalize similar content):
{downvoted_context}

Output your response as valid JSON:
{{
  "scored_nuggets": [
    {{
      "nugget_index": 0,
      "dimension_scores": {{
        "specificity": 75,
        "novelty": 60,
        "authority": 80,
        "actionability": 55,
        "story_energy": 70,
        "audience_resonance": 65
      }},
      "missing_fields": ["example", "steps"],
      "scoring_rationale": "Brief explanation"
    }}
  ]
}}
"""

# --- Dedup Decision Prompt v1 ---

DEDUP_DECISION_V1 = """You are deciding whether new nuggets duplicate existing knowledge graph nodes.

For each candidate nugget, decide:
- "create": This is genuinely new - create a new node
- "merge": This says the same thing as an existing node - merge them
- "link_expands": This adds depth to an existing node - link as expands_on
- "link_related": This is related but distinct - link as related_to

DECISION RULES:
1. PREFER "create" unless similarity is clear
2. "merge" only if the core insight is identical
3. "link_expands" if the new nugget adds examples, evidence, or depth
4. "link_related" if they share themes but are distinct insights

USER-EDITED NODES:
If a user has edited a node, they've invested in it. PREFER merging into user-edited nodes over raw extracted ones when appropriate.

Candidate nuggets:
{candidates_json}

Existing nodes (with user_edited flag):
{existing_nodes_json}

Embedding similarity scores (0-1):
{similarity_scores}

Output your response as valid JSON:
{{
  "decisions": [
    {{
      "nugget_index": 0,
      "outcome": "create" | "merge" | "link_expands" | "link_related",
      "existing_node_id": "uuid or null",
      "merge_rationale": "Why merge/link (null for create)",
      "similarity_score": 0.85
    }}
  ]
}}
"""

# --- Next Question Prompt v1 ---

NEXT_QUESTIONS_V1 = """You are generating the next-best questions to deepen a knowledge graph.

For each nugget, generate 1-2 questions that would:
- Fill the most critical gaps in the nugget
- Unlock additional valuable content
- Feel like a natural next step in conversation

QUESTION QUALITY:
- SPECIFIC: Reference the actual nugget content
- ACTIONABLE: Something the user can answer immediately
- VALUABLE: Would produce high-signal content

GAP TYPES:
- "example": Ask for a concrete example or case study
- "evidence": Ask for data, metrics, or proof
- "steps": Ask for the process or how-to
- "counterpoint": Ask about objections or edge cases
- "definition": Ask for clarification on key terms
- "audience": Ask who this applies to
- "outcome": Ask about results or impact

SCORE EACH QUESTION (0-100):
- impact: How valuable would the answer be?
- leverage: How much would this unlock other insights?
- momentum: Does this feel like a natural next step?
- connectivity: Will the answer connect to other nodes?
- gap_criticality: How critical is filling this gap?

Nuggets to generate questions for:
{nuggets_json}

Current graph context (themes and connections):
{graph_context}

Exclude nuggets with these IDs (downvoted):
{excluded_ids}

Output your response as valid JSON:
{{
  "candidates": [
    {{
      "question": "The specific question to ask",
      "target_nugget_index": 0,
      "gap_type": "example",
      "impact_score": 85,
      "leverage_score": 70,
      "momentum_score": 90,
      "connectivity_score": 60,
      "gap_criticality_score": 75
    }}
  ],
  "why_primary": "One sentence explaining why the top question is the best next step"
}}
"""

# --- Correction Prompt (for retries) ---

CORRECTION_PROMPT = """Your previous response did not match the required JSON schema.

Error: {error_message}

Please correct your response and output valid JSON matching this schema:
{schema_description}

Your previous response:
{previous_response}

Corrected response:
"""

# --- Prompt Registry ---

PROMPTS = {
    "extract_nuggets_v1": EXTRACT_NUGGETS_V1,
    "score_nuggets_v1": SCORE_NUGGETS_V1,
    "dedup_decision_v1": DEDUP_DECISION_V1,
    "next_questions_v1": NEXT_QUESTIONS_V1,
    "correction": CORRECTION_PROMPT,
}


def get_prompt(name: str) -> str:
    """Get a prompt by name."""
    if name not in PROMPTS:
        raise ValueError(f"Unknown prompt: {name}. Available: {list(PROMPTS.keys())}")
    return PROMPTS[name]
