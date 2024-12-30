import os
import sys
import json
from utils import read_file, write_file, delete_empty_lines, apply_changes_to_code, extract_changes_from_response, send_to_llm_streaming
from constants import CODE_BLOCK, INSTRUCTIONS_SUFFIX

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
            code = delete_empty_lines(code)
            code_blocks.append(code)
    return '\n\n'.join(code_blocks)

def apply_changes_to_codebase(project, changes):
    modified_files = {}
    
    for file in project['files']:
        if not file['included']:
            continue
            
        path = os.path.join(project['basePath'], file['name'])
        code = read_file(path)
        
        # Apply each change that matches this file's content
        for change in changes:
            if change['search'] in code:
                code = apply_changes_to_code(code, [change])
                modified_files[path] = code
    
    # Write all modified files
    for path, code in modified_files.items():
        write_file(path, code)

def list_files(project):
    print("\nCurrent files:")
    for i, file in enumerate(project['files']):
        status = "[x]" if file['included'] else "[ ]"
        print(f"{i}. {status} {file['name']} ({file['language']})")





if len(sys.argv) != 2:
    print("Usage: python script.py <project_id>")
    sys.exit(1)

project_id = sys.argv[1]
config = load_config()
project = get_project(config, project_id)

while True:
    list_files(project)
    user_instruction = input("\nEnter your instruction (number to toggle, 'quit' to exit): ")
    
    if user_instruction.lower() == 'quit':
        break
    
    # Check if input is a number for toggling files
    if user_instruction.isdigit():
        file_index = int(user_instruction)
        if toggle_file(project['files'], file_index):
            print(f"Toggled file {project['files'][file_index]['name']}")
        else:
            print("Invalid file index")
        continue

    # Get concatenated code from all included files
    code = get_concatenated_code(project)
    if not code.strip():
        print("No files are currently included!")
        continue

    # First LLM request - Analysis
    first_prompt = f"""
{CODE_BLOCK}
{code}
{CODE_BLOCK}
{user_instruction}
""".strip()

    print("\nAnalyzing changes needed:")
    analysis = send_to_llm_streaming(first_prompt)

    # Second LLM request - Generate search/replace blocks
    second_prompt = f"""
{CODE_BLOCK}
{code}
{CODE_BLOCK}

I have previously given the following prompt to an assistant: {user_instruction}

The assistant gave the following response:
{analysis}

{INSTRUCTIONS_SUFFIX}
""".strip()

    print("\nGenerating code changes:")
    try:
        changes_response = send_to_llm_streaming(second_prompt)
    except:
        print("ERROR: Could not generate code changes! Trying again")
        changes_response = send_to_llm_streaming(second_prompt)
    
    changes = extract_changes_from_response(changes_response)
    if changes:
        apply_changes_to_codebase(project, changes)
        print("\nChanges applied successfully!\n")
    else:
        print("ERROR: Could not find any search and replace pairs!")