import asyncio
import logging

import anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from src.models.content import PostVariant
from src.models.state import CreationPipelineState
from src.models.strategy import AccountNiche
from src.prompts.generation_prompts import GENERATE_VARIANTS_SYSTEM, GENERATE_VARIANTS_USER
from src.store.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class GenerationResult(BaseModel):
    variants: list[PostVariant] = Field(description="Exactly 5 post variants")


async def generate_post_variants(
    state: CreationPipelineState,
    *,
    llm: ChatAnthropic,
    kb: KnowledgeBase,
) -> dict:
    patterns = state.get("extracted_patterns", [])
    if not patterns:
        return {
            "generated_variants": [],
            "errors": ["generate_post_variants: No patterns available"],
        }

    niche_config, strategy, recent_posts, all_performances = await asyncio.gather(
        kb.get_niche_config(),
        kb.get_strategy(),
        kb.get_recent_posts(limit=10),
        kb.get_all_pattern_performances(),
    )
    niche = niche_config or AccountNiche()

    proven_patterns = sorted(
        [p for p in all_performances if p.times_used > 0],
        key=lambda p: p.effectiveness_score,
        reverse=True,
    )

    proven_text = ""
    if proven_patterns:
        proven_text = "\n\n".join(
            f"Pattern: {p.pattern_name} [PROVEN — {p.times_used} uses, "
            f"{p.avg_engagement_rate:.2%} avg ER, "
            f"effectiveness {p.effectiveness_score:.1f}/10]\n"
            f"(Use this pattern name exactly when generating a variant with it)"
            for p in proven_patterns[:5]
        )

    patterns_text = "\n\n".join(
        f"Pattern: {p.get('name', 'unnamed')} [NEW]\n"
        f"Description: {p.get('description', '')}\n"
        f"Structure: {p.get('structure', '')}\n"
        f"Hook type: {p.get('hook_type', '')}"
        for p in patterns
    )

    pillars_text = "No specific pillars configured."
    if niche.content_pillars:
        pillars_text = "\n".join(
            f"- {p.name} ({p.weight:.0%}): {p.description}" for p in niche.content_pillars
        )

    recent_text = (
        "\n".join(f"- {p.content[:100]}..." for p in recent_posts) or "No posts published yet."
    )

    avoid_text = ", ".join(niche.avoid_topics) if niche.avoid_topics else "None specified."

    strategy_text = (
        "\n".join(strategy.key_learnings)
        if strategy.key_learnings
        else "No learnings yet - first cycle."
    )

    structured_llm = llm.with_structured_output(GenerationResult)

    try:
        result = await structured_llm.ainvoke(
            [
                SystemMessage(content=GENERATE_VARIANTS_SYSTEM.format(niche=niche.niche)),
                HumanMessage(
                    content=GENERATE_VARIANTS_USER.format(
                        niche=niche.niche,
                        voice_tone=niche.voice.tone,
                        voice_persona=niche.voice.persona,
                        style_notes="\n".join(niche.voice.style_notes),
                        proven_patterns=proven_text or "No proven patterns yet — all exploration.",
                        new_patterns=patterns_text,
                        pillars=pillars_text,
                        avoid_topics=avoid_text,
                        recent_posts=recent_text,
                        strategy_learnings=strategy_text,
                    )
                ),
            ]
        )
    except (anthropic.APIError, OutputParserException, ValidationError) as e:
        logger.exception("LLM call failed in generate_post_variants")
        return {
            "generated_variants": [],
            "errors": [f"generate_post_variants: LLM call failed: {e}"],
        }

    return {"generated_variants": [v.model_dump() for v in result.variants]}
