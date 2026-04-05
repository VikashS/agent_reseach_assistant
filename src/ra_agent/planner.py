"""Planning module - converts user goals into structured TODO plans"""

import json
import textwrap
from ra_agent.llm import LLMClient
from ra_agent.prompts import PLANNING_PROMPT_TEMPLATE

from ra_agent.prompts import PLAN_CREATE_PROMPT_TEMPLATE

TEMPRATURE = 0.3
MAX_TOKENS = 1000


class Planner:
    """Creates structured plans from user goals"""

    def __init__(self):
        self.llm = LLMClient()

    def _build_planning_prompt(self, user_goal: str) -> str:
        """Build the planning prompt with clear instructions"""
        return textwrap.dedent(PLANNING_PROMPT_TEMPLATE.format(user_goal=user_goal)).strip()

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might have markdown wrapping"""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()

    def _fallback_plan(self, user_goal: str) -> list:
        """Fallback plan when LLM fails"""
        return [
            {"description": f"Search for information about: {user_goal[:50]}", "type": "search", "query": user_goal},
            {"description": "Summarize findings", "type": "summarize", "query": "Provide a summary of the research"},
        ]

    def create_plan(self, user_goal: str) -> list:
        """
        Convert user goal into a structured TODO plan

        Returns:
            List of tasks, each with: description, type, query
        """
        prompt = self._build_planning_prompt(user_goal)

        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": f"{PLAN_CREATE_PROMPT_TEMPLATE}"},
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPRATURE,
                max_tokens=MAX_TOKENS,
            )

            # Extract JSON from response
            plan_text = self._extract_json(response)
            plan = json.loads(plan_text)

            # Validate plan structure
            if not isinstance(plan, list):
                raise ValueError("Plan must be a list")

            # Ensure each task has required fields
            for task in plan:
                if "description" not in task:
                    task["description"] = "Unknown task"
                if "type" not in task:
                    task["type"] = "search"
                if "query" not in task and task["type"] in ["search", "read"]:
                    task["query"] = task["description"]

            return plan

        except json.JSONDecodeError as e:
            print(f"Failed to parse plan as JSON: {e}")
            print(f"Raw response: {plan_text}")
            return self._fallback_plan(user_goal)
        except Exception as e:
            print(f"Planning failed: {e}")
            return self._fallback_plan(user_goal)

