import openai
import os
from dotenv import load_dotenv
import bentoml
from bentoml.io import JSON

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Создаем BentoML сервис
@bentoml.service(name="ProPlants", traffic={"timeout": 300})
class ProPlantsService:
    
    @bentoml.api(input=JSON(), output=JSON())
    async def generate(self, input_json: dict) -> dict:
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
