EXTRACT_PATTERNS_SYSTEM = """\
You are an expert social media analyst specializing in viral content mechanics.
Your job is to analyze viral posts and extract reusable content patterns.

A "pattern" is a repeatable content structure or technique that drives engagement.
Focus on WHY posts go viral, not just WHAT they say."""

EXTRACT_PATTERNS_USER = """\
Analyze these viral posts from the {niche} niche and extract 3-5 distinct \
content patterns that explain their success.

## Viral Posts to Analyze

{viral_posts}

## Known Pattern Performance (historical data)

{pattern_performance}

## Instructions

For each pattern, provide:
1. A short, memorable name (e.g., "contrarian_hot_take", "numbered_list_thread")
2. A description of what makes it work psychologically
3. The structure/template (e.g., "Bold claim → Evidence → Question")
4. The hook type (question, bold_claim, story, stat, list, etc.)
5. 2-3 example hooks that use this pattern
6. Which content pillars it's best suited for
7. How many of the analyzed posts use this pattern

CRITICAL — Pattern naming rules:
- Look at the "Known Pattern Performance" list above FIRST.
- If a pattern you found is similar to an EXISTING pattern, you MUST reuse the \
exact same name (e.g., if "first_person_investigation" exists and you see a similar \
investigative-style pattern, use "first_person_investigation" — do NOT invent \
"personal_investigation_story" or any variation).
- Only create a NEW name if the pattern is genuinely different from all existing ones.
- This is essential for the learning system to accumulate data on patterns over time.

Focus on patterns that are:
- Replicable (can be used for different topics)
- Proven (seen in multiple successful posts)
- Suited to the {niche} niche"""
