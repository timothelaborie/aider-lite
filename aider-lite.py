import requests
import json
import os
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

def read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()

def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def delete_empty_lines(code):
    # if a line contains only white space, replace it with ""
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
    res = "\n".join(indented_lines)
    return res


def apply_changes(code, changes):
    for (j,change) in enumerate(changes):
        search = change['search']
        replace = change['replace']

        search = delete_empty_lines(search)
        replace = delete_empty_lines(replace)

        replaced_code = code.replace(search, replace)
        if replaced_code == code:
            # print(f"\n\nFailed to apply change {j+1}: adding spaces until a match is found")
            for i in range(10):
                search = add_indentation(search)
                replace = add_indentation(replace)
                replaced_code = code.replace(search, replace)
                if replaced_code != code:
                    # print(f"Match found after adding {i} indentations\n\n")
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
                # End of code block
                if 'search' not in current_change:
                    current_change['search'] = '\n'.join(code_block_content)
                else:
                    current_change['replace'] = '\n'.join(code_block_content)
                    changes.append(current_change)
                    current_change = {}
                in_code_block = False
                code_block_content = []
            else:
                # Start of code block
                in_code_block = True
        elif in_code_block:
            code_block_content.append(line)
    
    return changes

def send_to_llm_streaming(prompt):
    load_dotenv()
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1/",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    response = client.chat.completions.create(
        model=None,
        messages=[
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.0,
        extra_body={"route": "fallback", "models": ["anthropic/claude-3.5-sonnet:beta", "openai/gpt-4o"]}
    )

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content

    print()  # Add a newline after streaming is complete
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
        prompt_suffix = read_file("prompt.txt")
        prompt_suffix = prompt_suffix.replace("instruction_placeholder", user_instruction)
        prompt_suffix = prompt_suffix.replace("programming_language_placeholder", lang)
        
        full_prompt = f"""The current date is Tuesday, October 10th 2023, 10:30am
```{lang}
{code}
```

{prompt_suffix}"""
        
        print("LLM Response:")
        llm_response = send_to_llm_streaming(full_prompt)
        
        changes = extract_changes(llm_response)
        if changes:
            code = apply_changes(code, changes)
            write_file(path, code)
            print("\n\n\n")
        else:
            print("ERROR: Could not find any search and replace pairs!")

if __name__ == "__main__":
    main()