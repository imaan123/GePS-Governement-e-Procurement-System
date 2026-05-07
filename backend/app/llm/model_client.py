import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
PRIVATE_URL = "Provide private url here"


class QwenClient:

    def __init__(self, model="qwen2.5:7b", mode="local"):
        self.model = model
        self.mode = mode

    def generate(self, prompt: str) -> str:

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if self.mode == "local":
            url = OLLAMA_URL
            response = requests.post(url, json=payload)

            if response.status_code != 200:
                raise Exception(f"Model error: {response.text}")

            return response.json()["response"]
        else:
            url = PRIVATE_URL+f"?prompt={prompt}"
            headers = {"x-api-key": "your api key here"}
            response = requests.post(url, headers=headers)    
            if response.status_code != 200:
                raise Exception(f"Model error: {response.text}") 
            return response.json()["response"]