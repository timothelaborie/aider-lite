import sys
import os
import time
from utils import (extract_changes_from_response, send_to_llm_streaming, 
                  load_config, get_project, print_list_of_files, toggle_file, 
                  get_concatenated_code, apply_changes_to_codebase,
                  extract_first_codeblock, copy_to_clipboard,
                  delete_empty_lines_and_trailing_whitespace, read_file, write_file)
from constants import CODE_BLOCK, INSTRUCTIONS_SUFFIX, SAVE_HISTORY
import pyperclip

if len(sys.argv) != 2:
    print("Usage: python script.py <project_id>")
    sys.exit(1)

project_id = sys.argv[1]
config = load_config()
project = get_project(config, project_id)

# Clean up all project files at startup
print("Cleaning up files...")
files_modified = 0
for file in project['files']:
    path = os.path.join(project['basePath'], file['name'])
    original_content = read_file(path)
    cleaned_content = delete_empty_lines_and_trailing_whitespace(original_content)
    
    if original_content != cleaned_content:
        write_file(path, cleaned_content)
        files_modified += 1

if files_modified > 0:
    print(f"Cleaned up {files_modified} file(s) by removing empty lines and trailing whitespace.")
else:
    print("No files needed cleanup.")



# Main loop
while True:
    print_list_of_files(project)
    user_instruction = input("\nEnter your instruction (number to toggle, 'quit' to exit, '/clip' to use clipboard): ")
    
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

    # Check if it's a clipboard command
    use_clipboard = False
    if user_instruction.startswith('/clip '):
        use_clipboard = True
        user_instruction = user_instruction[6:]  # Remove '/clip ' prefix
        try:
            code = pyperclip.paste()
            if not code.strip():
                print("Clipboard is empty!")
                continue
        except Exception as e:
            print(f"Error accessing clipboard: {e}")
            continue
    else:
        # Get concatenated code from all included files
        code = get_concatenated_code(project)
        if not code.strip():
            print("No files are currently included!")
            continue

    # First LLM request - Analysis
    first_prompt = f"""
{code}
{user_instruction}
""".strip()

    print("\n\n*** Analyzing changes needed ***\n")
    analysis = send_to_llm_streaming(first_prompt)

    if SAVE_HISTORY:
        folder = os.path.join("history", time.strftime("%Y-%m-%d_%H-%M-%S"))
        os.makedirs(folder, exist_ok=True)
        def save_to_file(filename, content):
            with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
                f.write(content)
        save_to_file("prompt.txt", first_prompt)
        save_to_file("response.txt", analysis)
    
    # Ask user what to do next
    print("\n\nWhat would you like to do next?")
    print("1: Apply changes")
    print("2: Copy first code block to clipboard")
    print("3: Do nothing")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        # Second LLM request - Generate search/replace blocks
        second_prompt = f"""
{code}

I have previously given the following prompt to an assistant: {user_instruction}

The assistant gave the following response:
<response>
{analysis}
</response>


{INSTRUCTIONS_SUFFIX}
""".strip()

        print("\n\n*** Generating code changes ***\n")
        try:
            changes_response = send_to_llm_streaming(second_prompt)
        except:
            print("\n\n****** ERROR: Could not generate code changes! Trying again ******\n")
            changes_response = send_to_llm_streaming(second_prompt)
        
        if SAVE_HISTORY:
            save_to_file("changes_response.txt", changes_response)
        changes = extract_changes_from_response(changes_response)
        if changes:
            apply_changes_to_codebase(project, changes, include_all=use_clipboard)
            print("\n\n*** Changes applied where possible ***\n")
        else:
            print("\n\n****** ERROR: Could not find any search and replace pairs! ******\n")
    
    elif choice == "2":
        first_codeblock = extract_first_codeblock(analysis)
        if first_codeblock:
            if copy_to_clipboard(first_codeblock):
                print("First code block copied to clipboard!")
            else:
                print("Failed to copy to clipboard. Make sure pyperclip is installed.")
        else:
            print("No code block found to copy!")
    
    elif choice == "3":
        print("No action taken.")
    
    else:
        print("Invalid choice. No action taken.")