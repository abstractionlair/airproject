import click
import os
import json
from datetime import datetime
from anthropic import Anthropic, APIError, RateLimitError, BadRequestError
from anthropic.types import ContentBlock, MessageParam, ToolParam, ToolResultBlockParam

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

You and the associated code are still in development. When things do not seem as expected there is a good chance the reason is that we have a bug.
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
        
        print(f"ToolUseBlock structure: {content_block}")
        
        # Try to access tool_call or tool_calls
        if hasattr(content_block, 'tool_call'):
            tool_call = content_block.tool_call
        elif hasattr(content_block, 'tool_calls') and len(content_block.tool_calls) > 0:
            tool_call = content_block.tool_calls[0]
        else:
            print(f"Unexpected ToolUseBlock structure: {content_block}")
            return None
        
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
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
        print(f"Error in handle_tool_use: {str(e)}")
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
    
    conversations = list_files()
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

def process_response(response, filepath):
    tool_calls = []
    with open(filepath, 'a') as f:
        f.write(f"\n\n## Assistant\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for content in response.content:
            if content.type == 'text':
                f.write(content.text)
                print(content.text)
            elif content.type == 'tool_use':
                tool_calls.append(content)
    return tool_calls

def process_stream(stream, filepath):
    tool_calls = []
    with open(filepath, 'a') as f:
        f.write(f"\n\n## Assistant\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for text in stream.text_stream:
            print(text, end="", flush=True)
            f.write(text)
    
    if stream.messages[-1].content:
        for content_block in stream.messages[-1].content:
            if content_block.type == 'tool_use':
                tool_calls.append(content_block)
    
    return tool_calls

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
        MessageParam(role="user", content=content)
    ]

    tools = [
        ToolParam(
            name="read_file",
            description="Reads the contents of a file and returns it as a string.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path to the file to be read."
                    }
                },
                "required": ["filename"]
            }
        ),
        ToolParam(
            name="write_file",
            description="Writes the provided content to a file.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path to the file where the content will be written."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write into the file."
                    }
                },
                "required": ["filename", "content"]
            }
        ),
        ToolParam(
            name="append_file",
            description="Appends the provided content to the end of a file.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path to the file where the content will be appended."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to append to the file."
                    }
                },
                "required": ["filename", "content"]
            }
        ),
        ToolParam(
            name="delete_file",
            description="Deletes the specified file.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path to the file to be deleted."
                    }
                },
                "required": ["filename"]
            }
        ),
        ToolParam(
            name="list_files",
            description="Lists all files in the conversations directory.",
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
    ]
    
    try:
        if stream:
            while True:
                with client.messages.stream(
                        model="claude-3-sonnet-20240229",
                        max_tokens=1000,
                        system=BaseSPrompt,
                        messages=messages,
                        tools=tools
                ) as stream:
                    tool_calls = process_stream(stream, filepath)
                
                if not tool_calls:
                    break  # No more tool calls, we're done

                for tool_call in tool_calls:
                    tool_result = handle_tool_use(tool_call)
                    if tool_result:
                        print(f"Tool call structure: {tool_call}")
                        tool_call_id = tool_call.tool_call.id if hasattr(tool_call, 'tool_call') else tool_call.tool_calls[0].id if hasattr(tool_call, 'tool_calls') else None
                        if tool_call_id:
                            messages.append(MessageParam(
                                role="tool",
                                content=[
                                    ToolResultBlockParam(
                                        type="tool_result",
                                        tool_call_id=tool_call_id,
                                        content=tool_result
                                    )
                                ]
                            ))
                        else:
                            print(f"Unable to extract tool_call_id from: {tool_call}")
        else:
            while True:
                response = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    system=BaseSPrompt,
                    messages=messages,
                    tools=tools
                )

                tool_calls = process_response(response, filepath)
                
                if not tool_calls:
                    break  # No more tool calls, we're done

                for tool_call in tool_calls:
                    tool_result = handle_tool_use(tool_call)
                    if tool_result:
                        print(f"Tool call structure: {tool_call}")
                        tool_call_id = tool_call.tool_call.id if hasattr(tool_call, 'tool_call') else tool_call.tool_calls[0].id if hasattr(tool_call, 'tool_calls') else None
                        if tool_call_id:
                            messages.append(MessageParam(
                                role="tool",
                                content=[
                                    ToolResultBlockParam(
                                        type="tool_result",
                                        tool_call_id=tool_call_id,
                                        content=tool_result
                                    )
                                ]
                            ))
                        else:
                            print(f"Unable to extract tool_call_id from: {tool_call}")

    except BadRequestError as e:
        click.echo(f"Bad request: {e}")
    except RateLimitError as e:
        click.echo(f"Rate limit exceeded: {e}")
    except APIError as e:
        click.echo(f"API error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")
        
    click.echo("Response received and appended to the conversation file.")
    click.echo("You can now edit the file and submit again to continue the conversation.")

if __name__ == '__main__':
    cli()
    
