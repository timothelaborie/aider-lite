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

class CodeAssistant:
    def __init__(self, project):
        self.project = project
        self.history_folder = None

    def cleanup_project_files(self):
        print("Cleaning up files...")
        files_modified = 0
        for file in self.project['files']:
            path = os.path.join(self.project['basePath'], file['name'])
            original_content = read_file(path)
            cleaned_content = delete_empty_lines_and_trailing_whitespace(original_content)

            if original_content != cleaned_content:
                write_file(path, cleaned_content)
                files_modified += 1

        if files_modified > 0:
            print(f"Cleaned up {files_modified} file(s) by removing empty lines and trailing whitespace.")
        else:
            print("No files needed cleanup.")

    def handle_file_toggle(self, user_input):
        if not user_input.isdigit():
            return False

        file_index = int(user_input)
        if toggle_file(self.project['files'], file_index):
            print(f"Toggled file {self.project['files'][file_index]['name']}")
        else:
            print("Invalid file index")
        return True

    def get_code_for_analysis(self, user_instruction):
        use_clipboard = user_instruction.startswith('. ')
        if use_clipboard:
            instruction = user_instruction[2:]  # Remove '. ' prefix
            try:
                code = CODE_BLOCK + "\n" + pyperclip.paste() + "\n" + CODE_BLOCK
                if not code.strip():
                    print("Clipboard is empty!")
                    return None, None, None
            except Exception as e:
                print(f"Error accessing clipboard: {e}")
                return None, None, None
        else:
            instruction = user_instruction
            code = get_concatenated_code(self.project)
            if not code.strip():
                print("No files are currently included!")
                return None, None, None

        return code, instruction, use_clipboard

    def handle_copy_project(self):
        code = get_concatenated_code(self.project)
        pyperclip.copy(code)
        print("Whole project copied to clipboard!")

    def save_history(self, filename, content):
        if not SAVE_HISTORY:
            return

        if not self.history_folder:
            self.history_folder = os.path.join("history", time.strftime("%Y-%m-%d_%H-%M-%S"))
            os.makedirs(self.history_folder, exist_ok=True)

        with open(os.path.join(self.history_folder, filename), "w", encoding="utf-8") as f:
            f.write(content)

    def analyze_changes(self, code, instruction):
        prompt = f"{code}\n{instruction}".strip()

        print("\n\n*** Analyzing changes needed ***\n")
        analysis = send_to_llm_streaming([prompt], thinking=False, apply=False)

        self.save_history("prompt.txt", prompt)
        self.save_history("response.txt", analysis)

        return prompt, analysis

    def apply_changes_workflow(self, first_prompt, analysis, use_clipboard):
        second_prompt = INSTRUCTIONS_SUFFIX

        print("\n\n*** Generating code changes ***\n")
        changes_response = send_to_llm_streaming(
            [first_prompt, analysis, second_prompt],
            thinking=False,
            apply=True
        )

        self.save_history("changes_response.txt", changes_response)

        changes = extract_changes_from_response(changes_response)
        if changes:
            apply_changes_to_codebase(self.project, changes, include_all=use_clipboard)
            print("\n\n*** Changes applied where possible ***\n")
        else:
            print("\n\n****** ERROR: Could not find any search and replace pairs! ******\n")

    def copy_first_codeblock_workflow(self, analysis):
        first_codeblock = extract_first_codeblock(analysis)
        if first_codeblock:
            if copy_to_clipboard(first_codeblock):
                print("First code block copied to clipboard!")
            else:
                print("Failed to copy to clipboard. Make sure pyperclip is installed.")
        else:
            print("No code block found to copy!")

    def get_user_choice_after_analysis(self):
        print("\n\nWhat would you like to do next?")
        print("1: Apply changes")
        print("2: Copy first code block to clipboard")
        print("3: Do nothing")

        return input("Enter your choice: ")

    def handle_paste_changes(self):
        try:
            clipboard_content = pyperclip.paste()
            if not clipboard_content.strip():
                print("Clipboard is empty!")
                return
        except Exception as e:
            print(f"Error accessing clipboard: {e}")
            return

        print("\n\n*** Applying changes from clipboard ***\n")

        # Save the pasted content to history
        self.save_history("pasted_changes.txt", clipboard_content)

        # Extract changes from the clipboard content
        changes = extract_changes_from_response(clipboard_content)

        if changes:
            # Apply changes to all files (include_all=True since we're pasting specific changes)
            apply_changes_to_codebase(self.project, changes, include_all=True)
            print("\n\n*** Changes applied where possible ***\n")
        else:
            print("\n\n****** ERROR: Could not find any search and replace pairs in clipboard! ******\n")
            print("Make sure clipboard contains properly formatted code block pairs.")

    def process_instruction(self, user_instruction):
        if user_instruction == "copy":
            self.handle_copy_project()
            return

        if user_instruction == "paste":
            self.handle_paste_changes()
            return

        # Check if prompt starts with ", " and if yes, perform analysis
        do_analysis = user_instruction.startswith(', ')
        if do_analysis:
            user_instruction = user_instruction[2:]  # Remove ', ' prefix

        code, instruction, use_clipboard = self.get_code_for_analysis(user_instruction)
        if code is None:
            return

        if do_analysis:
            # Workflow with analysis
            first_prompt, analysis = self.analyze_changes(code, instruction)
            choice = self.get_user_choice_after_analysis()

            if choice == "1":
                self.apply_changes_workflow(first_prompt, analysis, use_clipboard)
            elif choice == "2":
                self.copy_first_codeblock_workflow(analysis)
            elif choice == "3":
                print("No action taken.")
            else:
                print("Invalid choice. No action taken.")

        else:
            # Skip analysis, go directly to changes generation
            first_prompt = f"{code}\n\nThe user prompt is:\n{instruction}\n\n\n{INSTRUCTIONS_SUFFIX}".strip()

            print("\n\n*** Generating code changes ***\n")
            changes_response = send_to_llm_streaming([first_prompt], thinking=True, apply=True)

            self.save_history("prompt.txt", first_prompt)
            self.save_history("changes_response.txt", changes_response)

            changes = extract_changes_from_response(changes_response)
            if changes:
                apply_changes_to_codebase(self.project, changes, include_all=use_clipboard)
                print("\n\n*** Changes applied where possible ***\n")
            else:
                print("\n\n****** ERROR: Could not find any search and replace pairs! ******\n")


    def run(self):
        self.cleanup_project_files()

        while True:
            print_list_of_files(self.project)
            user_instruction = input("\nEnter your instruction (number to toggle, 'quit' to exit, '.' to use clipboard, 'paste' to apply clipboard changes): ")

            if user_instruction.lower() == 'quit':
                break

            if self.handle_file_toggle(user_instruction):
                continue

            self.process_instruction(user_instruction)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    config = load_config()
    project = get_project(config, project_id)

    assistant = CodeAssistant(project)
    assistant.run()

if __name__ == "__main__":
    main()