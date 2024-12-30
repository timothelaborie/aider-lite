import os
import sys
from utils import read_file, write_file, delete_empty_lines, apply_changes_to_code, extract_changes_from_response, send_to_llm_streaming
from constants import CODE_BLOCK, INSTRUCTIONS_SUFFIX

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

{INSTRUCTIONS_SUFFIX}
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