import requests
import json


class LLMClient:
    """LLM client for Ollama"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.1:8b"

    def chat(self, messages, temperature=0.3, max_tokens=1000):
        """Send chat to Ollama and return response"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=200,
        )
        return response.json()["message"]["content"]


# To use OpenAI instead, uncomment below and comment above:
# from openai import OpenAI
# class LLMClient:
#     def __init__(self):
#         self.client = OpenAI(api_key="your-key")
#         self.model = "gpt-3.5-turbo"
#
#     def chat(self, messages, temperature=0.3, max_tokens=1000):
#         response = self.client.chat.completions.create(
#             model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
#         )
#         return response.choices[0].message.content
