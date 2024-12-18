import requests
import json
import os
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

model_list = ["anthropic/claude-3.5-sonnet:beta", "google/gemini-exp-1206", "openai/gpt-4o"]
prevent_lazyness_prefix = "The current date is Tuesday, October 8th 2024, 10:30am"

def read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()

def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def delete_empty_lines(code):
    code = re.sub(r"^\s+$", "", code, flags=re.MULTILINE)
    return code

def add_indentation(text):
    lines = text.split("\n")
    indented_lines = []
    for line in lines:
        if line.strip() != "":
            indented_lines.append("    " + line)
        else:
            indented_lines.append(line)
    return "\n".join(indented_lines)

def apply_changes(code, changes):
    for (j,change) in enumerate(changes):
        search = change['search']
        replace = change['replace']

        search = delete_empty_lines(search)
        replace = delete_empty_lines(replace)

        replaced_code = code.replace(search, replace)
        if replaced_code == code:
            for i in range(10):
                search = add_indentation(search)
                replace = add_indentation(replace)
                replaced_code = code.replace(search, replace)
                if replaced_code != code:
                    break
                if i == 9:
                    print(f"PROBLEM: Failed to apply change {j+1}: no match found after adding 10 indentations\n\n")

        code = replaced_code

    return code

def extract_changes(llm_response):
    changes = []
    current_change = {}
    in_code_block = False
    code_block_content = []
    
    for line in llm_response.split('\n'):
        if line.strip().startswith('```'):
            if in_code_block:
                if 'search' not in current_change:
                    current_change['search'] = '\n'.join(code_block_content)
                else:
                    current_change['replace'] = '\n'.join(code_block_content)
                    changes.append(current_change)
                    current_change = {}
                in_code_block = False
                code_block_content = []
            else:
                in_code_block = True
        elif in_code_block:
            code_block_content.append(line)
    
    return changes



def send_to_llm_streaming(prompt, id):
    load_dotenv()
    
    # Clone the model list and rearrange to put id at the front
    arranged_models = model_list.copy()
    if id < len(arranged_models):
        selected_model = arranged_models.pop(id)
        arranged_models.insert(0, selected_model)

    extra_body = {
        "route": "fallback",
        "models": arranged_models
    }

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1/",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )    

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": prevent_lazyness_prefix},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.0,

        # model=model_list[id],

        model=None,
        extra_body=extra_body,
    )

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content

    print()
    return full_response

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
        first_prompt = f"""```{lang}
{code}
```
{user_instruction}"""

        print("\nAnalyzing changes needed:")
        analysis = send_to_llm_streaming(first_prompt, id=0)

        # Second LLM request - Generate search/replace blocks
        second_prompt = f"""
```{lang}
{code}
```

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
        
        changes = extract_changes(changes_response)
        if changes:
            code = apply_changes(code, changes)
            write_file(path, code)
            print("\n\n\n")
        else:
            print("ERROR: Could not find any search and replace pairs!")

if __name__ == "__main__":
    main()