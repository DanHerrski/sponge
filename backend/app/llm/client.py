"""LLM client abstraction with retry logic and JSON validation."""

import json
import logging
import os
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.prompts import get_prompt

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")  # "openai", "anthropic", or "stub"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


class LLMError(Exception):
    """Error from LLM call."""

    pass


class ValidationRetryExhaustedError(Exception):
    """Validation failed after retry."""

    pass


async def _call_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call OpenAI API."""
    try:
        import openai

        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        raise LLMError(f"OpenAI API error: {e}") from e


async def _call_anthropic(prompt: str, model: str = "claude-3-haiku-20240307") -> str:
    """Call Anthropic API."""
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        raise LLMError(f"Anthropic API error: {e}") from e


async def _call_stub(prompt: str, model: str = "stub") -> str:
    """Return stub response for testing without API calls."""
    # Detect which prompt type based on content
    if "extracting high-signal knowledge nuggets" in prompt:
        return json.dumps(
            {
                "nuggets": [
                    {
                        "nugget_type": "idea",
                        "title": "Stub extracted insight from user input",
                        "summary": (
                            "This is a stub extraction. In production,"
                            " the LLM would extract real insights from"
                            " the user's message based on their"
                            " specific content and experience."
                        ),
                        "key_phrases": ["stub", "extraction"],
                        "confidence": "medium",
                    }
                ],
                "extraction_notes": "Stub mode - no LLM API configured",
            }
        )
    elif "scoring knowledge nuggets" in prompt:
        return json.dumps(
            {
                "scored_nuggets": [
                    {
                        "nugget_index": 0,
                        "dimension_scores": {
                            "specificity": 65,
                            "novelty": 55,
                            "authority": 60,
                            "actionability": 70,
                            "story_energy": 50,
                            "audience_resonance": 60,
                        },
                        "missing_fields": ["example", "evidence"],
                        "scoring_rationale": "Stub scoring - configure LLM for real scores",
                    }
                ]
            }
        )
    elif "deciding whether new nuggets duplicate" in prompt:
        return json.dumps(
            {
                "decisions": [
                    {
                        "nugget_index": 0,
                        "outcome": "create",
                        "existing_node_id": None,
                        "merge_rationale": None,
                        "similarity_score": 0.0,
                    }
                ]
            }
        )
    elif "generating the next-best questions" in prompt:
        return json.dumps(
            {
                "candidates": [
                    {
                        "question": "Can you give me a specific example of when this happened?",
                        "target_nugget_index": 0,
                        "gap_type": "example",
                        "impact_score": 80,
                        "leverage_score": 70,
                        "momentum_score": 85,
                        "connectivity_score": 60,
                        "gap_criticality_score": 75,
                    },
                    {
                        "question": "What was the outcome when you applied this?",
                        "target_nugget_index": 0,
                        "gap_type": "outcome",
                        "impact_score": 75,
                        "leverage_score": 65,
                        "momentum_score": 70,
                        "connectivity_score": 55,
                        "gap_criticality_score": 70,
                    },
                    {
                        "question": "Who specifically would benefit most from this insight?",
                        "target_nugget_index": 0,
                        "gap_type": "audience",
                        "impact_score": 65,
                        "leverage_score": 60,
                        "momentum_score": 75,
                        "connectivity_score": 50,
                        "gap_criticality_score": 60,
                    },
                ],
                "why_primary": (
                    "A concrete example would make this insight more compelling and memorable."
                ),
            }
        )
    else:
        return json.dumps({"error": "Unknown prompt type in stub mode"})


async def call_llm(prompt: str, model: str | None = None) -> str:
    """Call the configured LLM provider."""
    model = model or DEFAULT_MODEL

    if LLM_PROVIDER == "openai":
        return await _call_openai(prompt, model)
    elif LLM_PROVIDER == "anthropic":
        return await _call_anthropic(prompt, model)
    else:
        return await _call_stub(prompt, model)


def _extract_json(response: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass

    # Try extracting from generic code block
    if "```" in response:
        start = response.find("```") + 3
        # Skip language identifier if present
        newline = response.find("\n", start)
        if newline > start:
            start = newline + 1
        end = response.find("```", start)
        if end > start:
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass

    # Try finding JSON object in response
    start = response.find("{")
    end = response.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response: {response[:200]}...")


async def call_llm_with_schema(
    prompt_name: str,
    schema_class: type[T],
    prompt_vars: dict,
    model: str | None = None,
    max_retries: int = 1,
) -> T:
    """
    Call LLM with a named prompt and validate response against schema.

    Args:
        prompt_name: Name of the prompt template
        schema_class: Pydantic model to validate against
        prompt_vars: Variables to format into the prompt
        model: Optional model override
        max_retries: Number of retries on validation failure

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationRetryExhaustedError: If validation fails after all retries
        LLMError: If LLM call fails
    """
    prompt_template = get_prompt(prompt_name)
    prompt = prompt_template.format(**prompt_vars)

    response = await call_llm(prompt, model)
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            data = _extract_json(response)
            return schema_class.model_validate(data)
        except (ValueError, ValidationError) as e:
            last_error = e
            logger.warning(f"Validation failed on attempt {attempt + 1}: {e}")

            if attempt < max_retries:
                # Retry with correction prompt
                correction_prompt = get_prompt("correction").format(
                    error_message=str(e),
                    schema_description=schema_class.model_json_schema(),
                    previous_response=response[:1000],
                )
                response = await call_llm(correction_prompt, model)

    raise ValidationRetryExhaustedError(
        f"Failed to get valid response after {max_retries + 1} attempts: {last_error}"
    )
