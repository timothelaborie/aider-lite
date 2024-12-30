import sys
from utils import extract_changes_from_response, send_to_llm_streaming, load_config, get_project, list_files, toggle_file, get_concatenated_code, apply_changes_to_codebase
from constants import CODE_BLOCK, INSTRUCTIONS_SUFFIX

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

    print("\n\n*** Analyzing changes needed ***\n")
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

    print("\n\n*** Generating code changes ***\n")
    try:
        changes_response = send_to_llm_streaming(second_prompt)
    except:
        print("\n\n****** ERROR: Could not generate code changes! Trying again ******\n")
        changes_response = send_to_llm_streaming(second_prompt)
    
    changes = extract_changes_from_response(changes_response)
    if changes:
        apply_changes_to_codebase(project, changes)
        print("\n\n*** Changes applied where possible ***\n")
    else:
        print("\n\n****** ERROR: Could not find any search and replace pairs! ******\n")