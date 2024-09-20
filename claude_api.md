# Comprehensive Anthropic Python SDK Usage Guide

## 1. Installation and Setup

Install the SDK:
```
pip install anthropic
```

Initialize the client:
```python
from anthropic import Anthropic, AsyncAnthropic

client = Anthropic(api_key="your_api_key_here")
async_client = AsyncAnthropic(api_key="your_api_key_here")
```

## 2. Core Components

- `Anthropic`: Main synchronous client.
- `AsyncAnthropic`: Asynchronous client.
- `resources`: Submodules for API functionalities.
- `types`: Type definitions for requests and responses.
- `Stream` and `AsyncStream`: For handling streaming responses.
- `BaseModel`: Base class for SDK models, inheriting from Pydantic.

## 3. Key Functionalities

### 3.1 Messages

```python
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ],
    temperature=0.7,
    system="You are a helpful AI assistant."
)
print(message.content)
```

### 3.2 Streaming

```python
with client.messages.stream(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Tell me a story."}
    ]
) as stream:
    for chunk in stream:
        if chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
            print(chunk.delta.text, end="", flush=True)
```

### 3.3 Tool Use

Tool Use allows the model to use defined tools during its response generation. This is particularly useful for complex tasks that require external data or functions.

#### Defining Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]
```

#### Using Tools in Messages

```python
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    tools=tools
)

# Process the response content
for content in message.content:
    if content.type == "text":
        print(f"Text: {content.text}")
    elif content.type == "tool_use":
        print(f"Tool used: {content.name}")
        print(f"Tool input: {content.input}")

# Simulate tool execution
weather_data = {"temperature": 72, "condition": "sunny"}

# Send tool result back to the model
follow_up = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"},
        {"role": "assistant", "content": message.content},
        {
            "role": "user", 
            "content": [
                {
                    "type": "tool_result",
                    "tool_call_id": content.id,  # Use the id from the tool_use block
                    "name": "get_current_weather",
                    "content": json.dumps(weather_data)
                }
            ]
        }
    ]
)

# Process the follow-up response
for content in follow_up.content:
    if content.type == "text":
        print(f"Response: {content.text}")
```

### 3.4 Image Understanding

Claude can analyze images when provided in base64 format:

```python
import base64

with open("image.jpg", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
)
```

## 4. Important Types

- `MessageParam`: Represents a message in a conversation.
- `MessageCreateParams`: Parameters for creating a message.
- `Model`: Supported model names (e.g., "claude-3-opus-20240229", "claude-3-sonnet-20240229").
- `ContentBlock`: Represents different types of content (text, image, tool_use).
- `ToolParam`: Defines a tool that can be used by the model.

## 5. Error Handling

```python
from anthropic import BadRequestError, RateLimitError

try:
    result = client.messages.create(...)
except BadRequestError as e:
    print(f"Bad request: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement retry logic or backoff
```

## 6. Async Support

```python
async def example():
    async with async_client.messages.stream(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Tell me a story."}]
    ) as stream:
        async for chunk in stream:
            if chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
                print(chunk.delta.text, end="", flush=True)
```

## 7. Advanced Features

### 7.1 Token Counting

```python
token_count = client.count_tokens("Hello, world!")
print(f"Token count: {token_count}")
```

### 7.2 System Prompts

```python
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    system="You are a helpful AI assistant specialized in Python programming.",
    messages=[
        {"role": "user", "content": "How do I use list comprehensions?"}
    ]
)
```

### 7.3 Temperature and Top-p Sampling

```python
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Generate a creative story idea."}],
    temperature=0.9,  # Higher temperature for more randomness
    top_p=0.95  # Nucleus sampling
)
```

## 8. Best Practices

1. Model Selection:
   - Use "claude-3-opus-20240229" for complex tasks requiring deep understanding.
   - Use "claude-3-sonnet-20240229" for general-purpose tasks with a balance of capability and speed.
   - Use "claude-3-haiku-20240229" for simpler tasks requiring quick responses.

2. Prompt Engineering:
   - Be clear and specific in your prompts.
   - Use system prompts to set the context and behavior of the model.
   - Structure multi-turn conversations clearly with appropriate role assignments.

3. Error Handling:
   - Implement comprehensive error handling to manage various API errors.
   - Use exponential backoff for rate limit errors.

4. Streaming:
   - Use streaming for long-running tasks or real-time interactions.
   - Implement proper stream handling and closure.

5. Tool Use:
   - Define tools with clear descriptions and schemas.
   - Handle tool calls and results appropriately in your application logic.

6. Token Management:
   - Use the `count_tokens()` method to estimate token usage.
   - Be mindful of token limits for different models.

7. Security:
   - Never expose your API key in client-side code.
   - Implement proper authentication and authorization in your application.

8. Performance:
   - Use async methods for concurrent operations.
   - Implement caching where appropriate to reduce API calls.

9. Versioning:
   - Stay updated with the latest SDK version for new features and bug fixes.
   - Be aware of model version changes and their impact on your application.
   
