import openai
import os
from dotenv import load_dotenv
from bentoml import Service, HTTPServer
from bentoml.io import JSON

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

svc = Service(name="plantspro", runners=[])

@svc.api(input=JSON(), output=JSON())
async def generate(input_json: dict) -> dict:
    question = input_json.get("input", "")
    if not question:
        return {"error": "No input provided."}

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты бот-ботаник. Отвечай строго по делу."},
            {"role": "user", "content": question}
        ]
    )
    return {"answer": response.choices[0].message["content"]}
