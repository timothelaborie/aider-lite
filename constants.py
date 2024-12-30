from openai import OpenAI
import os

PREVENT_LAZINESS_PREFIX = "The current date is Tuesday, October 8th 2024, 10:30am"
CODE_BLOCK = "```"
MODEL_LIST = ["anthropic/claude-3.5-sonnet:beta", "google/gemini-exp-1206", "openai/gpt-4o"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
