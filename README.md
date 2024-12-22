# aider-lite
Lightweight version of [Aider](https://aider.chat/) meant for editing a single file in an existing repo.

# Features
The idea behind Aider is that you can ask an LLM to make changes in a code file and it will use search/replace commands so you don't have to copy paste anything.

Compared to the original, this remake uses a two-step process:

1. The LLM (Usually 3.5 Sonnet) is given a code block containing the entire file, followed by the user instruction. There is no system prompt, so the model can focus exclusively on solving the coding task.
2. A second request is sent with the code block first, then the previous prompt with the response from the first step, then some instructions on how to make search/replace blocks.

The instructions are simple and concise, so this tool uses far fewer tokens than the real Aider. The two-step approach allows the LLM to perform better by avoiding distracting instructions.

This tool works best when you have a large file where modifications often require changing multiple parts of it. For example, if you have a React app, you can split it up into a utils file and main file, where the utils file contains code that is rarely changed, the main file has everything else, and then use this tool on the main file.

# How to use
1. Create an env variable called OPENROUTER_API_KEY containing your openrouter key
2. Run aider-lite.py, with the first parameter being your file path and the second parameter being the programming language that the code block should have (for example "python").
3. Run the script
4. Write an instruction like "Add an API to obtain the list of documents" and press enter
5. Review the changes made by the LLM using something like Github Desktop
