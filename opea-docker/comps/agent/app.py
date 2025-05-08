import json
import requests
from duckduckgo_search import DDGS
from html2text import HTML2Text

def call_ollama_llm(model, messages, tools):
    """
    Sends a POST request to the locally hosted Ollama LLM.
    Adjust the URL if your service endpoint differs.
    """
    url = "http://localhost:8008/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"LLM request failed: {response.status_code} {response.text}")
    return response.json()

def search_web(query: str) -> list:
    results = DDGS().text(query, max_results=10)
    if results:
        return [
            {
                "title": result["title"],
                "url": result["href"]
            }
            for result in results
        ]
    return []

def get_page_content(url: str) -> str:
    response = requests.get(url)
    h = HTML2Text()
    h.ignore_links = False
    content = h.handle(response.text)
    return content[:4000] if len(content) > 4000 else content

def extract_vocabulary(text: str) -> list:
    words = set(text.lower().split())
    vocabulary = [word for word in words if word.isalpha()]
    return sorted(vocabulary)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the web for."
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": "Get the content of a web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_vocabulary",
            "description": "Extract new vocabulary from a text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to extract new vocabulary from."
                    }
                },
                "required": ["text"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Define languages and a sample Japanese song title.
user_language = "English"        # User's native language
foreign_language = "Japanese"      # Language being learned
song_title = "上を向いて歩こう"  # Example Japanese song

messages = [
    {
        "role": "system",
        "content": f"""
You are a helpful Japanese language tutor.
When the user provides a song title, search for the song lyrics and help them learn new vocabulary from it.
First search for the lyrics, then extract vocabulary from them.
Explain the meaning of new words in simple Japanese while also providing English explanations.
Focus on words that are valuable for a language learner.
The user's native language is {user_language} and they are learning {foreign_language}.
        """
    },
    {
        "role": "user",
        "content": f"Help me learn about the song '{song_title}'"
    }
]

goal_achieved = False
limit = 10
model = "llama3.2"

while not goal_achieved and len(messages) < limit:
    completion = call_ollama_llm(model=model, messages=messages, tools=tools)
    message = completion["choices"][0]["message"]
    messages.append(message)

    if "tool_calls" in message and message["tool_calls"]:
        for tool_call in message["tool_calls"]:
            # Parse the arguments provided by the LLM for the tool call.
            arguments = json.loads(tool_call["function"]["arguments"])
            if tool_call["function"]["name"] == "search_web":
                result = search_web(arguments["query"])
                print(f'Calling search_web with query: "{arguments["query"]}"')
                for item in result:
                    print(f'  - {item["title"]}')
            elif tool_call["function"]["name"] == "get_page_content":
                result = get_page_content(arguments["url"])
                print(f'Calling get_page_content with URL: "{arguments["url"]}"')
            elif tool_call["function"]["name"] == "extract_vocabulary":
                result = extract_vocabulary(arguments["text"])
                print('Calling extract_vocabulary on provided text snippet:')
                for word in result:
                    print(f"  - {word}")
            else:
                result = None

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "unknown"),
                "content": json.dumps(result)
            })
    else:
        goal_achieved = True

print("Final Message:")
print(messages[-1]["content"])