import requests

url = "http://localhost:9000/v1/chat/completions"
payload = {
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "test"}],
    "stream": False
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response Body:", response.text) 