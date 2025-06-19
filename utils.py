import os
import re
import json
from typing import List
from constants import CODER_MODELS, APPLY_MODELS, CODER_MODELS_THINKING, client, DEBUG, CODE_BLOCK
import tiktoken
enc = tiktoken.get_encoding("o200k_base")

def read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()

def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def delete_empty_lines_and_trailing_whitespace(code):
    # "empty lines" are lines with only whitespaces, they are made empty to avoid issues with the LLM
    return re.sub(r"[ \t]+$", "", code, flags=re.MULTILINE)

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
    any_changes_applied = False
    code = delete_empty_lines_and_trailing_whitespace(code)

    for (j,change) in enumerate(changes):
        search = change['search']
        replace = change['replace']

        search = delete_empty_lines_and_trailing_whitespace(search)
        replace = delete_empty_lines_and_trailing_whitespace(replace)

        replaced_code = code.replace(search, replace)
        if replaced_code == code:
            for i in range(10):
                search = add_indentation(search)
                replace = add_indentation(replace)
                replaced_code = code.replace(search, replace)
                if replaced_code != code:
                    any_changes_applied = True
                    break
        else:
            any_changes_applied = True

        code = replaced_code

    return code, any_changes_applied

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

def send_to_llm_streaming(prompts: List[str], thinking: bool, apply: bool) -> str:
    if DEBUG:
        with open("debug_output.txt", "r") as f:
            return f.read()

    # Alternate roles, starting with user
    roles = ["user", "assistant"]
    msg = [
        {"role": roles[i % 2], "content": p}
        for i, p in enumerate(prompts)
    ]

    if not thinking:
        response = client.chat.completions.create(
            messages=msg,
            stream=True,
            temperature=0.0,
            model=CODER_MODELS[0] if not apply else APPLY_MODELS[0],
        )
    else:
        response = client.chat.completions.create(
            messages=msg,
            stream=True,
            temperature=0.0,
            model=CODER_MODELS_THINKING[0],
            extra_body={
                "reasoning": {
                    "max_tokens": 3000
                }
            }
        )

    full_response = ""
    writing_reasoning = True
    for chunk in response:
        if chunk.choices[0].delta is not None:
            reasoning = ""
            try:
                reasoning = chunk.choices[0].delta.reasoning
            except AttributeError:
                pass
            content = chunk.choices[0].delta.content

            if reasoning is not None and len(reasoning) > 0:
                print(reasoning, end='', flush=True)

            if content is not None and len(content) > 0:
                if writing_reasoning:
                    if thinking:
                        print("\n\n\n\n\n\n\n\n", end='', flush=True)
                    writing_reasoning = False

                print(content, end='', flush=True)

            full_response += content

    print(f"\n\n\n\nTokens used: {len(enc.encode(' '.join(prompts)))}+{len(enc.encode(full_response))}\n")
    return full_response

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def get_project(config, project_id):
    for project in config['projects']:
        if project['id'] == project_id:
            return project
    raise ValueError(f"Project {project_id} not found in config")

def toggle_file(files, file_index):
    if 0 <= file_index < len(files):
        files[file_index]['included'] = not files[file_index]['included']
        return True
    return False

def get_concatenated_code(project):
    code_blocks = []
    for file in project['files']:
        if file['included']:
            name = file['name']
            path = os.path.join(project['basePath'], name)
            lang = file['language']
            code = read_file(path)
            code = delete_empty_lines_and_trailing_whitespace(code)
            code = f"""{name}:
{CODE_BLOCK}{lang}
{code}
{CODE_BLOCK}"""
            code_blocks.append(code)
    return '\n\n'.join(code_blocks)

def apply_changes_to_codebase(project, changes, include_all = False):
    # First read all files into memory
    files_content = {}
    for file in project['files']:
        if not file['included'] and not include_all:
            continue

        path = os.path.join(project['basePath'], file['name'])
        files_content[path] = read_file(path)

    # Process each change across all files
    for change in changes:
        print(f"\nApplying change: {change['search'].replace('\n', ' ')[:20]}...")
        change_success = False

        # Apply this change to all files
        for path, code in files_content.items():
            print(f"Processing file: {os.path.basename(path)}")
            newcode, success = apply_changes_to_code(code, [change])
            files_content[path] = newcode
            if success:
                change_success = True
                print("Change applied successfully!")
                break

        if not change_success:
            print("Change could not be applied to any file!")

    # Write all modified files
    for path, code in files_content.items():
        write_file(path, code)


def print_list_of_files(project):
    print("\nCurrent files:")
    for i, file in enumerate(project['files']):
        status = "[x]" if file['included'] else "[ ]"
        print(f"{i}. {status} {file['name']} ({file['language']})")


def extract_first_codeblock(text):
    """Extract the first code block from text."""
    in_code_block = False
    code_lines = []

    for line in text.split('\n'):
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                continue
            else:
                in_code_block = False
                return '\n'.join(code_lines)
        if in_code_block:
            code_lines.append(line)

    return ""  # Return empty string if no code block found

def copy_to_clipboard(text):
    """Copy text to clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False