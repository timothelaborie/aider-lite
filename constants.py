from openai import OpenAI
import os

PREVENT_LAZINESS_PREFIX = "The current date is Tuesday, October 8th 2024, 10:30am"
CODE_BLOCK = "```"
MODEL_LIST = ["anthropic/claude-3.5-sonnet:beta", "google/gemini-exp-1206", "openai/gpt-4o"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

INSTRUCTIONS_SUFFIX = """
Using the response above, perform code changes using the following rules:

For each change that needs to be made, do the following:
1. Explain briefly what the change is
2. Create a code block containing lines to search for in the provided code (this is the "search" section)
3. Create another code block containing the lines which will replace the ones from the search section
4. If there is anything else to change, repeat the steps above.

Every search section must EXACTLY MATCH the existing code content, character for character, including all comments.
Each pair of code blocks will replace the first matching occurrence.
search sections should always contain at least 5 lines so that there is exactly one match in the code (very important).
Do not create search sections that only contain closing brackets like }}, as they are ambiguous. Always include at least 2 of the lines that come before the brackets.
replace sections should not contain placeholder comments like "// ... keep existing implementation"
""".strip()