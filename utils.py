import os
import re
import json
from constants import PREVENT_LAZINESS_PREFIX, MODEL_LIST, client, DEBUG

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

def send_to_llm_streaming(prompt:str) -> str:
    if DEBUG:
        with open("debug_output.txt", "r") as f:
            return f.read()
  
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
            path = os.path.join(project['basePath'], file['name'])
            code = read_file(path)
            code = delete_empty_lines_and_trailing_whitespace(code)
            code_blocks.append(code)
    return '\n\n'.join(code_blocks)

def apply_changes_to_codebase(project, changes):
    # First read all files into memory
    files_content = {}
    for file in project['files']:
        if not file['included']:
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


def list_files(project):
    print("\nCurrent files:")
    for i, file in enumerate(project['files']):
        status = "[x]" if file['included'] else "[ ]"
        print(f"{i}. {status} {file['name']} ({file['language']})")