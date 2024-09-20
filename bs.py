import os
import sys
import openai
import json
import shutil
from datetime import datetime

# Constants
TARGET_FILE = sys.argv[0]  # The current script is the target file
HISTORY_FILE = 'airproject_history.json'

# Get OpenAI API key from environment variable
openai.api_key = os.environ.get('OPENAI_API_KEY')

def read_file(filename):
    """Reads the contents of the specified file."""
    print(f"Function 'read_file' called with filename: {filename}")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"'read_file' successfully read {len(content)} characters from {filename}.")
        return content
    except Exception as e:
        print(f"Error in 'read_file': {e}")
        return ""

def write_file(content, filename):
    """Writes the provided content to the specified file."""
    print(f"Function 'write_file' called with filename: {filename}")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"'write_file' successfully wrote content to {filename}.")
    except Exception as e:
        print(f"Error in 'write_file': {e}")

def get_user_input():
    """Prompts the user for input."""
    return input("Please enter your request:\n")

def load_conversation_history():
    """Loads the conversation history from the JSON file."""
    print(f"Loading conversation history from {HISTORY_FILE}...")
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        print(f"Loaded conversation history with {len(history)} entries.")
        return history
    except json.JSONDecodeError:
        print(f"Error: {HISTORY_FILE} is corrupted. Starting with empty history.")
        return []
    except Exception as e:
        print(f"Unexpected error while loading history: {e}")
        return []

def save_conversation_history(history):
    """Saves the conversation history to the JSON file."""
    temp_file = f"{HISTORY_FILE}.temp"
    print(f"Saving conversation history to {HISTORY_FILE}...")
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        # If successful, replace the original file
        shutil.move(temp_file, HISTORY_FILE)
        print("Conversation history saved successfully.")
    except Exception as e:
        print(f"Error saving conversation history: {str(e)}")
        # In case of error, remove the temporary file if it exists
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Temporary file {temp_file} removed due to error.")

def log_conversation(history, new_message):
    """Logs the conversation to the history."""
    new_entry = {"timestamp": datetime.now().isoformat()}
    new_entry.update(new_message)
    print("New entry:", new_entry)
    history.append(new_entry)
    save_conversation_history(history)

def log_error(history, error_message):
    """Logs an error to the history."""
    print(f"Logging error: {error_message}")
    log_conversation(history, {"role": "error", "content": error_message})

def main():
    print("Main function started.")
    
    # System prompt explaining the AI's role and available functions
    system_prompt = """You are an AI assistant designed to improve and modify the code contained in a set of files controlled by the user. You have access to two functions:

1. read_file(filename): Returns the contents of the specified file.
2. write_file(content, filename): Writes the provided content to the specified file.

Use these functions to read and suggest modifications to the code as necessary based on the user's requests. Ensure that any changes you suggest are functional and improve the code's performance, readability, and security. Your suggestions will be written to a separate file for review.

Your goal is to help improve the tool's code based on the user's input. Remember to maintain the code's existing functionality unless instructed otherwise."""
    print("System prompt initialized.")

    # Load conversation history and get user input
    history = load_conversation_history()
    messages = [{'role': 'system', 'content': system_prompt}]
    print("System message added to messages.")
    for msg in history:
        if msg['role'] != 'error':
            #messages.append({'role': msg['role'], 'content': msg['content']})
            messages.append(msg)
    print(f"Added {len(history)} historical messages to current messages.")

    user_input = get_user_input()
    new_message = {'role': 'user', 'content': user_input}
    messages.append(new_message)
    log_conversation(history, new_message)
    print("User message appended to messages and logged.")

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
    print("AI functions defined and ready.")

    # Interact with the AI assistant
    while True:
        print("Sending request to OpenAI ChatCompletion API...")
        try:
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
            print("Response received from OpenAI API.")
        except Exception as e:
            error_message = f"An error occurred while communicating with OpenAI API: {str(e)}"
            print(error_message)
            print("messages:", messages)
            log_error(history, error_message)
            break

        assistant_message = response['choices'][0]['message']
        messages.append(assistant_message)
        print(f"Assistant message added to messages. Role: {assistant_message.get('role')}")

        if assistant_message.get('function_call'):
            function_call = assistant_message['function_call']
            function_name = function_call['name']
            try:
                arguments = json.loads(function_call.get('arguments', '{}'))
                print(f"Assistant requested function call: {function_name} with arguments: {arguments}")
            except json.JSONDecodeError:
                error_message = "Failed to decode function call arguments."
                print(error_message)
                log_error(history, error_message)
                break

            # Execute the function
            if function_name == 'read_file':
                print(f"Executing function 'read_file' with filename: {arguments['filename']}")
                result = read_file(arguments['filename'])
            elif function_name == 'write_file':
                print(f"Executing function 'write_file' with filename: {arguments['filename']}")
                write_file(arguments['content'], arguments['filename'])
                result = f"Content written to {arguments['filename']} successfully."
            else:
                result = f"Error: Function '{function_name}' not recognized."
                print(result)

            # Append the function's result to the messages
            print("Appending function result to messages.")
            print("Function Name:", function_name)
            print("Result:", result)
            new_message = {
                'role': 'function',
                'name': function_name,
                'content': result}
            messages.append(new_message)
            log_conversation(history, new_message)
            print("Function result logged and appended. Continuing the loop.")
            # After executing the function, loop again to let the assistant continue
            continue
        else:
            # No function call, output the assistant's reply
            assistant_reply = assistant_message.get('content', '')
            log_conversation(history, assistant_message)
            print("\nAssistant:", assistant_reply)
            print("No function call detected. Exiting the loop.")
            break  # Exit the loop

    print("Main function completed.")

if __name__ == "__main__":
    main()
