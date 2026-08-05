import json
import os
from anthropic import Anthropic, CLAUDE_3_SONNET

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# File paths
CONVERSATION_FILE = "conversation.json"
TARGET_FILE = "target.py"

def load_conversation():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r") as f:
            return json.load(f)
    return []

def save_conversation(conversation):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump(conversation, f, indent=2)

def read_target_file():
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r") as f:
            return f.read()
    return ""

def write_target_file(content):
    with open(TARGET_FILE, "w") as f:
        f.write(content)

def get_system_prompt():
    return """You are a Python coding assistant. You can read and write to a file named 'target.py'.
Use the read_target_file tool to check the current content of the file, and the 
write_target_file tool to update its content. Provide clear explanations of your actions."""

def chat_with_claude(conversation):
    response = anthropic.messages.create(
        model=CLAUDE_3_SONNET,
        max_tokens=1024,
        messages=conversation,
        system=get_system_prompt(),
        tools=[
            {
                "name": "read_target_file",
                "description": "Read the content of target.py",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "write_target_file",
                "description": "Write content to target.py",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file"
                        }
                    },
                    "required": ["content"]
                }
            }
        ]
    )
    
    # Process tool calls
    for content in response.content:
        if content.type == 'tool_call':
            tool_call = content.tool_call
            if tool_call.name == "read_target_file":
                file_content = read_target_file()
                conversation.append({"role": "tool", "name": "read_target_file", "content": file_content})
            elif tool_call.name == "write_target_file":
                write_target_file(tool_call.arguments['content'])
                conversation.append({"role": "tool", "name": "write_target_file", "content": "File updated successfully"})
        elif content.type == 'text':
            return content.text
    
    # If we only got tool calls and no text response, call Claude again
    return chat_with_claude(conversation)

def main():
    conversation = load_conversation()
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        
        conversation.append({"role": "user", "content": user_input})
        response = chat_with_claude(conversation)
        print(f"Claude: {response}")
        conversation.append({"role": "assistant", "content": response})
        save_conversation(conversation)

if __name__ == "__main__":
    main()
