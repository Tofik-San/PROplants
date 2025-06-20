import os
from dotenv import load_dotenv
import openai
from typing import Dict
from bentoml.io import JSON
from bentoml import Service, Runnable, runnable, Tag, api

# Загружаем .env
load_dotenv()

# Получаем API-ключ
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not найден в переменных окружения.")

client = openai.OpenAI(api_key=api_key)

# Создаём Bento-сервис
svc = Service("plantspro", runners=[])

@svc.api(input=JSON(), output=JSON())
def generate_plant_response(input_data: Dict) -> Dict:
    query = input_data.get("query", "Расскажи о растении.")
    prompt = f"Ответь на вопрос о растениях: {query}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content.strip()
    return {"response": answer}
