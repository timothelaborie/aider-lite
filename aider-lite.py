import os
import sys
from utils import read_file, write_file, delete_empty_lines, apply_changes_to_code, extract_changes_from_response, send_to_llm_streaming
from constants import CODE_BLOCK

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_file> <lang>")
        sys.exit(1)

    path = sys.argv[1]
    lang = sys.argv[2]

    while True:
        user_instruction = input("Enter your instruction (or 'quit' to exit): ")
        if user_instruction.lower() == 'quit':
            break
        
        code = read_file(path)
        code = delete_empty_lines(code)

        # First LLM request - Analysis
        first_prompt = f"""{CODE_BLOCK}{lang}
{code}
{CODE_BLOCK}
{user_instruction}"""

        print("\nAnalyzing changes needed:")
        analysis = send_to_llm_streaming(first_prompt)

        # Second LLM request - Generate search/replace blocks
        second_prompt = f"""
{CODE_BLOCK}{lang}
{code}
{CODE_BLOCK}

I have previously given the following prompt to an assistant: {user_instruction}

The assistant gave the following response:
{analysis}

Using the response above, perform code changes using the following rules:

For each change that needs to be made, do the following:
1. Explain briefly what the change is
2. Create a {lang} code block containing lines to search for in the provided code (this is the "search" section)
3. Create another code block containing the lines which will replace the ones from the search section
4. If there is anything else to change, repeat the steps above.

Every search section must EXACTLY MATCH the existing code content, character for character, including all comments.
Each pair of code blocks will replace the first matching occurrence.
search sections should always contain at least 5 lines so that there is exactly one match in the code (very important).
Do not create search sections that only contain closing brackets like }}, as they are ambiguous. Always include at least 2 of the lines that come before the brackets.
replace sections should not contain placeholder comments like "// ... keep existing implementation"
""".strip()

        print("\nGenerating code changes:")
        try:
            changes_response = send_to_llm_streaming(second_prompt, id=0)
        except:
            print("ERROR: Could not generate code changes! Trying again")
            changes_response = send_to_llm_streaming(second_prompt, id=0)
        
        changes = extract_changes_from_response(changes_response)
        if changes:
            code = apply_changes_to_code(code, changes)
            write_file(path, code)
            print("\n\n\n")
        else:
            print("ERROR: Could not find any search and replace pairs!")

if __name__ == "__main__":
    main()