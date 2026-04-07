"""Neural Perception Layer.

LLM-based intent parsing for intelligent mode. Default provider is Anthropic
(claude-haiku-4-5 by default). OpenAI is supported as a swap. If neither key
is configured, falls back to the deterministic rule-based parser.
"""
from __future__ import annotations

import json
import logging

from src.config import settings
from src.models import ParsedIntent, UserContext
from src.resolution.intent_rules import parse_intent_rules

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are an enterprise data concept parser. Extract structured intent from "
    "business queries. Return ONLY a JSON object with these keys:\n"
    '  "concepts": object mapping concept_type -> raw value mentioned in the query\n'
    '  "intent_type": one of "lookup", "comparison", "trend", "anomaly"\n'
    '  "complexity": one of "simple", "multi_metric", "cross_domain", "novel"\n\n'
    "Concept types: metric, dimension, time, comparison, aggregation, filter.\n"
    "Be precise. Only extract what is explicitly mentioned. Do not invent values."
)


class NeuralPerceptionLayer:
    """Wraps Claude/GPT to parse natural-language queries into ParsedIntent."""

    async def parse_intent(self, query: str, user_ctx: UserContext) -> ParsedIntent:
        """Try the configured LLM provider; fall back to rules on any failure."""
        try:
            if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
                return await self._parse_with_anthropic(query, user_ctx)
            if settings.llm_provider == "openai" and settings.openai_api_key:
                return await self._parse_with_openai(query, user_ctx)
        except Exception as exc:
            logger.warning(
                "neural.parse_intent failed (%s); falling back to rule parser", exc
            )

        return parse_intent_rules(query)

    async def _parse_with_anthropic(self, query: str, user_ctx: UserContext) -> ParsedIntent:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.llm_model,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"User department: {user_ctx.department or 'unknown'}\n"
                        f"Query: {query}\n\n"
                        "Return JSON only."
                    ),
                }
            ],
        )
        text = response.content[0].text.strip()
        # Strip markdown fences if Claude wraps the JSON.
        if text.startswith("```"):
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(text)
        return ParsedIntent(**parsed)

    async def _parse_with_openai(self, query: str, user_ctx: UserContext) -> ParsedIntent:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User department: {user_ctx.department or 'unknown'}\n"
                        f"Query: {query}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=400,
        )
        parsed = json.loads(response.choices[0].message.content)
        return ParsedIntent(**parsed)
