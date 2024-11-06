# aider-lite
Lightweight version of Aider meant for editing a single file in an existing repo.

# Features
The idea behind Aider is that you can ask an LLM to make changes in a code file and it will use search/replace commands so you don't have to copy paste anything.

Compared to the [original](https://github.com/paul-gauthier/aider), this remake has a much more simple and concise system prompt, so it uses far fewer tokens. The prompt also has fewer distractions, so the LLM can perform better.

Another benefit is you don't have to add your file to the chat every time you launch it.

# How to use
1. Run aider-lite.py, with the first parameter being your file path and the second parameter being the programming language (used for the code block).
2. Create an env variable called OPENROUTER_API_KEY containing your openrouter key
3. Run the script
4. Write an instruction like "Add an API to obtain the list of documents" and press enter
5. Review the changes made by the LLM using something like Github Desktop
