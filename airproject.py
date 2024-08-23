@cli.command()
@click.argument('filename')
def submit(filename):
    """Submit a conversation file to Claude and append the response"""
    ensure_project_initialized()
    
    filepath = f"conversations/{filename}"
    if not os.path.exists(filepath):
        click.echo(f"Conversation file '{filename}' not found.")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    system_message = """
You are an AI assistant specialized in software development. You have access to the following file operation tools:

1. read_file(filename): Use this to read the contents of a file in the project. Use when you need to inspect code or documentation.
2. write_file(filename, content): Use this to create a new file or overwrite an existing file. Use cautiously, mainly for creating new files or when explicitly asked to replace file contents.
3. append_file(filename, content): Use this to add content to the end of an existing file. Prefer this over write_file when adding new content to preserve existing data.
4. delete_file(filename): Use this to delete a file. Use with extreme caution and only when explicitly instructed by the user.
5. list_files(): Use this to get a list of all files in the project. Use when you need an overview of the project structure.

Guidelines for using these tools:
- Always confirm with the user before making significant changes to files.
- Use read_file to understand the current state of files before modifying them.
- Prefer append_file over write_file unless you're certain the entire file needs to be replaced.
- Use delete_file only when explicitly instructed by the user.
- When writing or appending code, ensure it's properly formatted and commented.
- After performing file operations, summarize what you've done for the user.

Your primary role is to assist with software development tasks, answer questions, and provide guidance. Use these tools to help you in this role, but remember that your expertise and advice are the main value you provide.
"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": content}
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"{name.replace('_', ' ').capitalize()}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content": {"type": "string"} if name in ['write_file', 'append_file'] else {}
                    },
                    "required": ["filename"] + (["content"] if name in ['write_file', 'append_file'] else [])
                }
            }
        }
        for name in ['read_file', 'write_file', 'append_file', 'delete_file', 'list_files']
    ]
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=messages,
        tools=tools
    )
    
    # Handle potential function calls
    while response.content[0].type == 'function_call':
        function_result = handle_function_call(response.content[0].function_call)
        messages.append({
            "role": "function",
            "name": response.content[0].function_call['name'],
            "content": function_result
        })
        # Make another API call with the function result
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=messages,
            tools=tools
        )
    
    with open(filepath, 'a') as f:
        f.write(f"\n\n# Claude's response ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n")
        f.write(response.content[0].text)
    
    click.echo("Response received and appended to the conversation file.")
    click.echo("You can now edit the file and submit again to continue the conversation.")
