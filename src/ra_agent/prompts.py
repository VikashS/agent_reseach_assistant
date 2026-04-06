PLAN_CREATE_PROMPT_TEMPLATE = """You are a planning assistant. Output ONLY valid JSON."""

PLANNING_PROMPT_TEMPLATE = """
Break down this user goal into a sequence of 2-5 concrete tasks.
User goal: "{user_goal}"
Available task types:
- "search": For finding information online (needs a search query)
- "read": For reading content from a specific URL (needs URL)
- "summarize": For synthesizing information from previous tasks
- "ask_user": For requesting clarification or confirmation

Output format: JSON array of tasks, each with:
{{
    "description": "Clear description of what to do",
    "type": "search|read|summarize|ask_user",
    "query": "search query or URL or what to summarize"
}}

Example for "research Panda vs Pyspark":
[
    {{
        "description": "Find main differences between Panda and Pyspark",
        "type": "search",
        "query": "Panda vs Pyspark differences comparison"
    }},
    {{
        "description": "Research learning curve for each language",
        "type": "search", 
        "query": "Panda vs Pyspark learning curve for beginners"
    }},
    {{
        "description": "Summarize findings with recommendation",
        "type": "summarize",
        "query": "Compare Panda and Pyspark based on search results"
    }}
]

Generate a plan for the user's goal. Output ONLY the JSON array, no other text.
"""


GENERATE_FINAL_OUTPUT = """Create a final, user-friendly report answering the original goal.
                  Original goal: {user_goal}
                  Research findings:
                  {context}
                  Provide a clear, organized response with:
                  1. Executive summary (1-2 sentences)
                  2. Key findings (bullet points)
                  3. Actionable recommendations (if applicable)
                  Keep it concise but informative."""
