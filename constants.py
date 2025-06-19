from openai import OpenAI
import os

SAVE_HISTORY = True
CODE_BLOCK = "```"

APPLY_MODELS = ["anthropic/claude-sonnet-4","openai/gpt-4.1"]
CODER_MODELS = ["openai/gpt-4.1","anthropic/claude-sonnet-4",]
CODER_MODELS_THINKING = ["anthropic/claude-sonnet-4","google/gemini-2.5-pro-preview"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

INSTRUCTIONS_SUFFIX = """
Perform code changes using the following rules:

For each change that needs to be made, do the following:
1. Explain briefly what the change is
2. Create a code block containing lines to search for in the provided code (this is the "search" section)
3. Create another code block containing the lines which will replace the ones from the search section
4. If there is anything else to change, repeat the steps above.

Every search section must EXACTLY MATCH the existing code content, character for character, including all comments.
Each pair of code blocks will replace the first matching occurrence.
search sections should always contain at least 5 lines so that there is exactly one match in the code (very important).
Do not create search sections that only contain closing brackets like }}, as they are ambiguous. Always include at least 2 of the lines that come before the brackets.
"replace" sections should not contain placeholder comments like "// ... keep existing implementation" or conversational comments like "// <-- add this"
""".strip()

DEBUG = False