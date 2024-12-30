import os
import re
import sys
from openai import OpenAI
from constants import PREVENT_LAZINESS_PREFIX, MODEL_LIST, client

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

def apply_changes_to_code(code, changes):
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

def extract_changes_from_response(llm_response):
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

def send_to_llm_streaming(prompt:str) -> str:
  
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": PREVENT_LAZINESS_PREFIX},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.0,
        # model=model_list[0],
        model=None,
        extra_body={"route": "fallback","models": MODEL_LIST},
    )

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content

    print()
    return full_response