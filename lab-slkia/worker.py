import json
import requests

URL = "http://192.168.1.8:8000/v1/chat/completions"
MODEL = "qwen3-coder-30b"

with open("microtasks.json") as f:
    microtasks = json.load(f)

review = []

for task in microtasks:

    prompt = f"""
    Tarea:
    {task["goal"]}

    Resultado esperado:
    {task["expected_result"]}
    """
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500
    }

    response = requests.post(URL, json=payload)

    data = response.json()

    answer = data["choices"][0]["message"]["content"]

    review.append({
        "id": task["id"],
        "answer": answer
    })

    task["status"] = "REVIEW"


    
with open("review.json", "w") as f:
    json.dump(review, f, indent=4)


with open("microtasks.json", "w") as f:
    json.dump(microtasks, f, indent=4)