from openai import OpenAI
import json
import os

# Set your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths for conversation history and target Python file
CONVERSATION_FILE = "conversation.json"
TARGET_PYTHON_FILE = "target.py"

# Define the system prompt (system message)
SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a coding assistant. Help the user with writing, reviewing, and improving Python code. You have access to the target Python file and can read or write to it when necessary."
}

# Function to load the conversation history
def load_conversation():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Warning: conversation.json is empty or malformed. Starting with a new conversation.")
                return [SYSTEM_PROMPT]
    # Start the conversation with the system prompt if no history exists
    return [SYSTEM_PROMPT]

# Function to save the conversation history
def save_conversation(conversation):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump(conversation, f, indent=4)

# Function to read from the target Python file
def read_target_file():
    if os.path.exists(TARGET_PYTHON_FILE):
        with open(TARGET_PYTHON_FILE, "r") as f:
            return f.read()
    return ""

# Function to write to the target Python file
def write_target_file(content):
    with open(TARGET_PYTHON_FILE, "w") as f:
        f.write(content)

# Function to interact with OpenAI API using the updated API
def interact_with_openai(prompt, conversation):
    functions = [
        {
            "name": "read_target_file",
            "description": "Reads the content of the target Python file.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "write_target_file",
            "description": "Writes the content to the target Python file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The Python code to write to the file."
                    }
                },
                "required": ["content"]
            }
        }
    ]

    # Use the correct method for chat-based completions
    response = client.chat.completions.create(model="gpt-4o",
    messages=conversation,
    functions=functions,
    function_call="auto")

    message = response.choices[0].message
    print(message)


    if message.function_call is not None:
        function_name = message.function_call.name
        function_args = message.function_call.arguments

        # Call the appropriate function
        if function_name == "read_target_file":
            content = read_target_file()
            conversation.append({"role": "function", "name": "read_target_file", "content": content})
        elif function_name == "write_target_file":
            function_args = json.loads(function_args)
            print()
            print("Function args")
            print(type(function_args))
            print(function_args)
            content = function_args.get("content", "")
            write_target_file(content)
            conversation.append({"role": "function", "name": "write_target_file", "content": "File updated."})
    else:
        message_dict = message.model_dump()    
        conversation.append(message_dict)

    # Save the updated conversation
    save_conversation(conversation)

    return message.content

# Main function to append queries and interact with OpenAI
def main():
    # Load conversation history
    conversation = load_conversation()

    # Get user input (your query)
    user_input = input("Enter your query: ")

    # Append user input to the conversation
    conversation.append({"role": "user", "content": user_input})

    # Interact with OpenAI and get the assistant's response
    response = interact_with_openai(user_input, conversation)

    # Print the assistant's response
    print(response)

if __name__ == "__main__":
    main()


