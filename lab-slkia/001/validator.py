import json
import requests

URL = "http://192.168.1.8:8000/v1/chat/completions"
MODEL = "qwen3-coder-30b"

with open("review.json") as f:
    reviews = json.load(f)

with open("microtasks.json") as f:
    microtasks = json.load(f)

for review in reviews:

    for task in microtasks:

        if task["id"] == review["id"]:

            prompt = f"""
Validation:
{task["validation"]}

Answer:
{review["answer"]}

Respondé solamente:
PASS
o
FAIL
"""

            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 10
            }

            response = requests.post(URL, json=payload)
            data = response.json()

            result = data["choices"][0]["message"]["content"].strip()

            print("\nTASK:", task["id"])
            print("RESULT:", result)
