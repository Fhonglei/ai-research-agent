import json
from typing import Optional
from anthropic import Anthropic
from config import config
from utils.logger import logger


class TaskDecomposer:
    """
    Breaks a broad research topic into manageable subtopics using Claude.

    The decomposition is guided by structured prompts that instruct Claude to
    think like a senior research analyst, identifying distinct angles, domain
    areas, and key questions that together provide comprehensive coverage.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the task decomposer.

        Args:
            api_key: Anthropic API key. Falls back to config.
            model: Claude model to use. Falls back to config.MODEL.
        """
        self.client = Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY)
        self.model = model or config.MODEL
        logger.info(f"TaskDecomposer initialized with model={self.model}")

    def decompose(self, topic: str, depth: str = "standard") -> list[str]:
        """
        Decompose a research topic into a list of subtopics.

        Args:
            topic: The main research topic.
            depth: Research depth — "quick", "standard", or "deep".
                   Controls the number of subtopics (3-4, 4-6, or 5-7).

        Returns:
            A list of subtopic strings. Returns an empty list on failure.
        """
        if not topic or not topic.strip():
            logger.warning("decompose called with empty topic")
            return []

        # Determine target number of subtopics based on depth
        depth_config = {
            "quick": (3, 4),
            "standard": (4, 6),
            "deep": (5, 7),
        }
        min_sub, max_sub = depth_config.get(depth, (4, 6))

        prompt = self._build_prompt(topic, min_sub, max_sub, depth)

        try:
            logger.info(f"Decomposing topic (depth={depth}): '{topic[:100]}...'")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                system=(
                    "You are a senior research analyst with expertise across multiple domains. "
                    "Your task is to break a broad research topic into distinct, non-overlapping "
                    "subtopics that together provide comprehensive coverage. Each subtopic should "
                    "represent a meaningful angle of investigation — think about historical context, "
                    "current state, future trends, key players, technological aspects, economic "
                    "factors, social impact, regulatory environment, and competing perspectives. "
                    "Subtopic titles should be clear, concise, and self-contained (understandable "
                    "without the parent topic)."
                ),
                messages=[{"role": "user", "content": prompt}],
            )

            raw_output = response.content[0].text
            subtopics = self._parse_subtopics(raw_output)

            # Enforce count bounds
            if len(subtopics) < min_sub:
                logger.warning(
                    f"Got only {len(subtopics)} subtopics (min {min_sub}), using what we got"
                )
            elif len(subtopics) > max_sub:
                subtopics = subtopics[:max_sub]

            logger.info(f"Decomposed into {len(subtopics)} subtopics: {subtopics}")
            return subtopics

        except Exception as e:
            logger.error(f"Task decomposition failed for topic '{topic[:80]}...': {e}")
            # Fallback: simple word-based splitting
            return self._fallback_decompose(topic, min_sub)

    def _build_prompt(self, topic: str, min_sub: int, max_sub: int, depth: str) -> str:
        """Build the structured prompt for Claude."""
        return f"""Research Topic: {topic}
Research Depth: {depth.upper()}

As a senior research analyst, break this topic down into {min_sub}-{max_sub} distinct subtopics.
Each subtopic should explore a different dimension of the main topic.

Guidelines:
- Cover diverse angles: historical background, current developments, key stakeholders,
  technological aspects, economic impact, future outlook, challenges, and opportunities.
- Each subtopic should be specific enough to research independently.
- Avoid overlap between subtopics.
- Write subtopics as clear, descriptive phrases (not questions).

IMPORTANT: Return your response as a JSON array of strings ONLY. No markdown, no explanation,
no additional text. Example format:

["Subtopic One Description", "Subtopic Two Description", "Subtopic Three Description"]"""

    def _parse_subtopics(self, raw_output: str) -> list[str]:
        """
        Parse Claude's response into a list of subtopic strings.

        Handles JSON array format and fallback line-by-line parsing.
        """
        raw_output = raw_output.strip()

        # Try JSON parse first
        try:
            # Remove markdown code fences if present
            if raw_output.startswith("```"):
                lines = raw_output.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                raw_output = "\n".join(lines).strip()
            parsed = json.loads(raw_output)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

        # Fallback: try to extract a JSON array from within the text
        import re
        match = re.search(r"\[.*?\]", raw_output, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        # Last resort: parse numbered or bulleted lines
        subtopics = []
        for line in raw_output.split("\n"):
            line = line.strip()
            # Remove common prefixes: "1.", "- ", "* ", "1) "
            line = re.sub(r"^\d+[\.\)]\s*", "", line)
            line = line.lstrip("-* ").strip()
            if len(line) > 5 and line not in subtopics:
                subtopics.append(line)

        return subtopics

    def _fallback_decompose(self, topic: str, count: int) -> list[str]:
        """
        Generate generic subtopics as a fallback when the API call fails.
        """
        templates = [
            f"Overview and Background of {topic}",
            f"Current State and Key Developments in {topic}",
            f"Major Players and Stakeholders in {topic}",
            f"Challenges and Risks Related to {topic}",
            f"Future Outlook and Trends for {topic}",
            f"Economic and Market Impact of {topic}",
            f"Regulatory and Policy Landscape for {topic}",
        ]
        return templates[:count]
