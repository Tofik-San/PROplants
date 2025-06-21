import bentoml
from bentoml.io import JSON
import openai
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
svc = bentoml.Service("plantspro_service")

@svc.api(input=JSON(), output=JSON())
def generate(data):
    template_text = data.get("template", "")
    additions = data.get("additions", "")

    messages = [
        {"role": "system", "content": template_text},
        {"role": "user", "content": additions}
    ]

    try:
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return {"reply": chat.choices[0].message.content.strip()}
    except Exception as e:
        return {"reply": f"Ошибка при генерации: {e}"}

