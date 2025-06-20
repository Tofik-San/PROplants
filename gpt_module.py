# gpt_module.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_gpt_response(template_text: str, detail: str, task: str, goal: str) -> str:
    additions = (
        f"Роль: {detail}\n"
        f"Задача: {task}\n"
        f"Результат: {goal}"
    )

    messages = [
        {"role": "system", "content": template_text},
        {"role": "user", "content": additions}
    ]

    try:
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при генерации ответа: {e}"
