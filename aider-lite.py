import requests
import json
import os
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

def read_file(filename):
    with open(filename, "r") as file:
        return file.read()

def write_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)

def apply_changes(code, changes):
    for change in changes:
        search_pattern = re.escape(change['search'])

        # Check if the search pattern is only spaces and closing brackets
        if re.match(r'^\s*}$', change['search']):
            code = re.sub(search_pattern, change['replace'], code, count=1, flags=re.DOTALL)
        else:
            code = re.sub(search_pattern, change['replace'], code, flags=re.DOTALL)

        # If no match was found, try with 4 extra spaces
        if search_pattern not in code:
            indented_search_pattern = re.escape('    ' + change['search'])
            code = re.sub(indented_search_pattern, change['replace'], code, flags=re.DOTALL)

    return code

def send_to_llm_streaming(prompt):
    load_dotenv()
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1/",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.0,
    )

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content

    print()  # Add a newline after streaming is complete
    return full_response

def extract_changes(llm_response):
    changes = []
    pattern = r'>>>>>>SEARCH\n(.*?)\n=======\n(.*?\n)<<<<<<REPLACE'
    matches = re.findall(pattern, llm_response, re.DOTALL)
    
    for match in matches:
        changes.append({
            'search': match[0].strip(),
            'replace': match[1].strip()
        })
    
    return changes

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
        prompt_suffix = read_file("prompt.txt")
        prompt_suffix = prompt_suffix.replace("instruction_placeholder", user_instruction)
        
        full_prompt = f"""```{lang}
{code}
```

{prompt_suffix}"""
        
        print("LLM Response:")
        llm_response = send_to_llm_streaming(full_prompt)
        
        changes = extract_changes(llm_response)
        if changes:
            code = apply_changes(code, changes)
            write_file(path, code)
            print("Changes applied")
        else:
            print("No changes to apply")

if __name__ == "__main__":
    main()