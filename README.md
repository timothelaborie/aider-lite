# aider-lite
Lightweight version of [Aider](https://aider.chat/) meant for editing multiple files in an existing repo.

# Features
The idea behind Aider is that you can ask an LLM to make changes in code files and it will use search/replace commands so you don't have to copy paste anything.

Compared to the original, this remake has very concise instructions to avoid distracting the model, uses far fewer tokens, and is designed so you can configure it once in advance and then start coding right away after launching the tool.

This tool works best when you have multiple files where modifications often require changing several parts across them. You can select which files to include in each editing session.

## Commands

| Command | Description |
|---------|-------------|
| `<number>` | Toggle a file's inclusion by its index |
| `<instruction>` | Send an instruction to the LLM and apply the resulting changes |
| `. <instruction>` | Use clipboard content instead of project files as context |
| `opus <instruction>` | Use Claude Opus instead of the default model |
| `copy` | Copy all selected files to clipboard |
| `copy2` | Copy the search/replace instruction suffix to clipboard |
| `paste` | Apply search/replace blocks from clipboard to all project files |
| `paste2` | Apply search/replace blocks from clipboard to selected files only |
| `clear` | Deselect all files |
| `quit` | Exit the program |

## Clipboard Integration

The `copy` and `paste` commands allow you to use external LLM interfaces (like a web UI) as an alternative workflow:
1. `copy` your project files to clipboard
2. Paste them into an external LLM along with your instruction
3. Copy the LLM's response containing search/replace blocks
4. `paste` to apply the changes

The `. ` prefix lets you send clipboard content (e.g. code copied from elsewhere) as context instead of your project files.

# How to use
1. Create an env variable called `OPENROUTER_API_KEY` containing your OpenRouter key
2. Create a `config.json` file with your projects (see example below)
3. Run: `python aider-lite.py <project-id>`
4. Toggle which files to include by entering their number
5. Write an instruction like "Add an API to obtain the list of documents" and press enter
6. Review the changes made by the LLM using something like GitHub Desktop

Example `config.json`:
```json
{
  "projects": [
    {
      "id": "my-project",
      "basePath": "/path/to/project",
      "files": [
        {
          "name": "utils.py",
          "language": "python",
          "included": false
        },
        {
          "name": "main.py",
          "language": "python",
          "included": true
        }
      ]
    }
  ]
}
```
