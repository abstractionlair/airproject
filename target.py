import os
import sys
import openai
import json
import shutil
from datetime import datetime

# Constants
TARGET_FILE = sys.argv[0]  # The current script is the target file
HISTORY_FILE = 'airproject_history.json'
SUGGESTED_CHANGES_FILE = 'suggested_changes.py'

# Get OpenAI API key from environment variable
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")
    exit(1)

def read_file(filename):
    """Reads the contents of the specified file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(content, filename):
    """Writes the provided content to the specified file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def get_user_input():
    """Prompts the user for input."""
    return input("Please enter your request:\n")

def load_conversation_history():
    """Loads the conversation history from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {HISTORY_FILE} is corrupted. Starting with empty history.")
        return []

def save_conversation_history(history):
    """Saves the conversation history to the JSON file."""
    temp_file = f"{HISTORY_FILE}.temp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        # If successful, replace the original file
        shutil.move(temp_file, HISTORY_FILE)
    except Exception as e:
        print(f"Error saving conversation history: {str(e)}")
        # In case of error, remove the temporary file if it exists
        if os.path.exists(temp_file):
            os.remove(temp_file)

def log_conversation(history, role, content):
    """Logs the conversation to the history."""
    timestamp = datetime.now().isoformat()
    history.append({
        "timestamp": timestamp,
        "role": role,
        "content": content
    })
    save_conversation_history(history)

def log_error(history, error_message):
    """Logs an error to the history."""
    log_conversation(history, "error", error_message)

def main():
    # System prompt explaining the AI's role and available functions
    system_prompt = """You are an AI assistant designed to improve and modify the code contained in the target file. You have access to two functions:

1. read_file(filename): Returns the contents of the specified file.
2. write_file(content, filename): Writes the provided content to the specified file.

Use these functions to read and suggest modifications to the code as necessary based on the user's requests. Ensure that any changes you suggest are functional and improve the code's performance, readability, and security. Your suggestions will be written to a separate file for review.

Your goal is to help improve the tool's code based on the user's input. Remember to maintain the code's existing functionality unless instructed otherwise."""

    # Load conversation history and get user input
    history = load_conversation_history()
    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend([{'role': msg['role'], 'content': msg['content']} for msg in history if msg['role'] != 'error'])
    
    try:
        user_input = get_user_input()
        messages.append({'role': 'user', 'content': user_input})
        log_conversation(history, 'user', user_input)

        # Define the functions available to the AI
        functions = [
            {
                "name": "read_file",
                "description": "Reads the contents of the specified file and returns it as a string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to read."
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "write_file",
                "description": "Writes the provided content to the specified file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file."
                        },
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to write to."
                        }
                    },
                    "required": ["content", "filename"]
                }
            }
        ]

        # Interact with the AI assistant
        while True:
            response = openai.ChatCompletion.create(
                model="gpt-4o-2024-05-13",
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=0.7,
                max_tokens=1500,
                n=1,
                stop=None,
            )

            assistant_message = response['choices'][0]['message']
            messages.append(assistant_message)

            if assistant_message.get('function_call'):
                function_call = assistant_message['function_call']
                function_name = function_call['name']
                arguments = json.loads(function_call.get('arguments', '{}'))

                # Execute the function
                if function_name == 'read_file':
                    result = read_file(arguments['filename'])
                elif function_name == 'write_file':
                    write_file(arguments['content'], arguments['filename'])
                    result = f"Content written to {arguments['filename']} successfully."
                else:
                    result = f"Error: Function '{function_name}' not recognized."

                # Append the function's result to the messages
                messages.append({
                    'role': 'function',
                    'name': function_name,
                    'content': result
                })
                log_conversation(history, 'function', f"{function_name}: {result}")
                # After executing the function, loop again to let the assistant continue
                continue
            else:
                # No function call, output the assistant's reply
                assistant_reply = assistant_message['content']
                log_conversation(history, 'assistant', assistant_reply)
                print("\nAssistant:", assistant_reply)
                break  # Exit the loop

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(history, error_message)

if __name__ == "__main__":
    main()