import click
import os
import json
from datetime import datetime
from anthropic import Anthropic, APIError, RateLimitError, BadRequestError
from anthropic.types import ContentBlock, Message, MessageStreamEvent

BaseSPrompt = """
### Shared Part of System Prompt ###
You are an AI assistant integrated into a system for working on multiple projects.
Projects include such things as developing software applications or writing books or papers.
In any conversation you will be working with one specific project and be able to read and write its files.
Your role is to provide context-aware assistance within the specific project.
Your responses should be tailored to the project's context, audience, and goals.

When interacting within a project, follow these guidelines:
* Reference and utilize the project-specific files provided to inform your responses.
* Adhere to any custom instructions or preferences set for the project (e.g. tone, perspective, format).
* Generate or alter files like code, diagrams, or text documents when requested. By default, format these for easy viewing and editing.
* Provide expert-level assistance across various domains based on the project's focus (e.g. writing, coding, analysis).
* Offer suggestions for improving project workflows or highlighting relevant insights from project materials.

Your goal is to enhance productivity and collaboration by providing highly relevant, context-aware assistance tailored to each unique project environment.
"""

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=ANTHROPIC_API_KEY)

@click.group()
def cli():
    """AI-Assisted Software Development Tool"""
    pass

def ensure_project_initialized():
    if not os.path.exists('.aiproject.json'):
        click.echo("Project not initialized. Run 'aiproject init' first.")
        exit(1)

# CRUD Operations
def read_file(filename):
    filepath = os.path.join('conversations', filename)
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found."
    with open(filepath, 'r') as f:
        return f.read()

def write_file(filename, content):
    filepath = os.path.join('conversations', filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return f"Successfully wrote to '{filename}'."

def append_file(filename, content):
    filepath = os.path.join('conversations', filename)
    with open(filepath, 'a') as f:
        f.write(content)
    return f"Successfully appended to '{filename}'."

def delete_file(filename):
    filepath = os.path.join('conversations', filename)
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found."
    os.remove(filepath)
    return f"Successfully deleted '{filename}'."

def list_files():
    return os.listdir('conversations')

def handle_tool_use(content_block: ContentBlock):
    try:
        if content_block.type != 'tool_use':
            return None
        
        function_name = content_block.text
        arguments = json.loads(content_block.tool_calls[0].parameters)
        
        if function_name == 'read_file':
            return read_file(arguments['filename'])
        elif function_name == 'write_file':
            return write_file(arguments['filename'], arguments['content'])
        elif function_name == 'append_file':
            return append_file(arguments['filename'], arguments['content'])
        elif function_name == 'delete_file':
            return delete_file(arguments['filename'])
        elif function_name == 'list_files':
            return json.dumps(list_files())
        else:
            return f"Error: Unknown function '{function_name}'"
    except json.JSONDecodeError:
        return "Error: Invalid JSON in tool call arguments"
    except KeyError as e:
        return f"Error: Missing required argument {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

@cli.command()
def init():
    """Initialize a new project in the current directory"""
    if os.path.exists('.aiproject.json'):
        click.echo("Project already initialized.")
        return
    
    project_config = {
        "name": os.path.basename(os.getcwd()),
        "created_at": datetime.now().isoformat()
    }
    
    with open('.aiproject.json', 'w') as f:
        json.dump(project_config, f, indent=2)
    
    os.makedirs('conversations', exist_ok=True)
    
    click.echo("Project initialized successfully.")

@cli.command()
def list():
    """List all conversations in the project"""
    ensure_project_initialized()
    
    conversations = os.listdir('conversations')
    if not conversations:
        click.echo("No conversations found.")
        return
    
    click.echo("Conversations:")
    for conversation in conversations:
        click.echo(f"- {conversation}")

@cli.command()
@click.argument('filename')
def new(filename):
    """Create a new conversation file"""
    ensure_project_initialized()
    
    filepath = os.path.join('conversations', filename)
    if os.path.exists(filepath):
        click.echo(f"Conversation file '{filename}' already exists.")
        return
    
    with open(filepath, 'w') as f:
        f.write(f"# Conversation: {filename}\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## User\n")
        f.write("Enter your message here.\n")
    
    click.echo(f"New conversation file '{filename}' created.")
    click.echo("You can now edit the file and use 'aiproject submit' to start the conversation.")

@cli.command()
@click.argument('filename')
@click.option('--stream', is_flag=True, help="Use streaming for the response")
def submit(filename, stream):
    """Submit a conversation file to Claude and append the response"""
    ensure_project_initialized()
    
    filepath = os.path.join('conversations', filename)
    if not os.path.exists(filepath):
        click.echo(f"Conversation file '{filename}' not found.")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    messages = [
        {
            "role": "user",
            "content": content
        }
    ]
    
    tools = [
        # ... (keep the existing tool definitions)
    ]

    try:
        if stream:
            with client.messages.stream(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                system=BaseSPrompt,
                messages=messages,
                tools=tools
            ) as stream:
                with open(filepath, 'a') as f:
                    f.write(f"\n\n## Assistant\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for chunk in stream:
                    if isinstance(chunk, MessageStreamEvent):
                        if chunk.type == "content_block_start":
                            current_block = chunk.content_block
                        elif chunk.type == "content_block_delta":
                            if chunk.delta.type == "text_delta":
                                print(chunk.delta.text, end="", flush=True)
                                with open(filepath, 'a') as f:
                                    f.write(chunk.delta.text)
                        elif chunk.type == "content_block_stop":
                            if hasattr(current_block, 'type') and current_block.type == 'tool_use':
                                tool_result = handle_tool_use(current_block)
                                if tool_result:
                                    messages.append({
                                        "role": "tool",
                                        "name": current_block.text,
                                        "content": tool_result
                                    })
                                    # Re-create the stream with updated messages
                                    stream = client.messages.stream(
                                        model="claude-3-opus-20240229",
                                        max_tokens=1000,
                                        system=BaseSPrompt,
                                        messages=messages,
                                        tools=tools
                                    )
        else:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                system=BaseSPrompt,
                messages=messages,
                tools=tools
            )

            with open(filepath, 'a') as f:
                f.write(f"\n\n## Assistant\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for content in response.content:
                    if hasattr(content, 'type'):
                        if content.type == 'text':
                            f.write(content.text)
                            print(content.text)
                        elif content.type == 'tool_use':
                            tool_result = handle_tool_use(content)
                            if tool_result:
                                messages.append({
                                    "role": "tool",
                                    "name": content.text,
                                    "content": tool_result
                                })
                                # Make another API call with the tool result
                                response = client.messages.create(
                                    model="claude-3-opus-20240229",
                                    max_tokens=1000,
                                    system=BaseSPrompt,
                                    messages=messages,
                                    tools=tools
                                )
                                # Continue processing the new response

    except BadRequestError as e:
        click.echo(f"Bad request: {e}")
    except RateLimitError as e:
        click.echo(f"Rate limit exceeded: {e}")
    except APIError as e:
        click.echo(f"API error: {e}")
    
    click.echo("Response received and appended to the conversation file.")
    click.echo("You can now edit the file and submit again to continue the conversation.")
    
if __name__ == '__main__':
    cli()
    
