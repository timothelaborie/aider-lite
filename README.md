# aider-lite
Lightweight version of [Aider](https://aider.chat/) meant for editing multiple files in an existing repo.

# Features
The idea behind Aider is that you can ask an LLM to make changes in code files and it will use search/replace commands so you don't have to copy paste anything.

Compared to the original, this remake uses a two-step process:

1. The LLM (Usually Claude 3.7 Sonnet) is given code blocks containing the content of selected files, followed by the user instruction. There is no system prompt, so the model can focus exclusively on solving the coding task.
2. A second request is sent with the code blocks first, then the previous prompt with the response from the first step, then some instructions on how to make search/replace blocks.

The instructions are simple and concise, so this tool uses far fewer tokens than the real Aider. The two-step approach allows the LLM to perform better by avoiding distracting instructions.

This tool works best when you have multiple files where modifications often require changing several parts across them. You can select which files to include in each editing session.

# How to use
1. Create an env variable called OPENROUTER_API_KEY containing your OpenRouter key
2. Create a config.json file with your projects (see example below)
3. Run aider-lite.py with the project ID as a parameter: `python aider-lite.py my-project`
4. Toggle which files to include by entering their number
5. Write an instruction like "Add an API to obtain the list of documents" and press enter
6. Review the changes made by the LLM using something like Github Desktop

Example config.json:
```json
{
  "projects": [
    {
      "id": "my-project",
      "basePath": "/path/to/project",
      "files": [
        {
          "name": "main.py",
          "language": "python",
          "included": true
        },
        {
          "name": "utils.py",
          "language": "python",
          "included": false
        }
      ]
    }
  ]
}
```