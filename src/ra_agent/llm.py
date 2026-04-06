import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

# class LLMClient:
#     """LLM client for Ollama"""
#
#     def __init__(self):
#         load_dotenv()
#         self.base_url = "http://localhost:11434"
#         self.model = "llama3.1:8b"
#
#     def chat(self, messages, temperature=0.3, max_tokens=1000):
#         """Send chat to Ollama and return response"""
#         response = requests.post(
#             f"{self.base_url}/api/chat",
#             json={
#                 "model": self.model,
#                 "messages": messages,
#                 "stream": False,
#                 "options": {"temperature": temperature, "num_predict": max_tokens},
#             },
#             timeout=200,
#         )
#         return response.json()["message"]["content"]


##To use OpenAI instead, uncomment below all
from openai import OpenAI


class LLMClient:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL")

    def chat(self, messages, temperature=0.3, max_tokens=1000):
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        return response.choices[0].message.content
