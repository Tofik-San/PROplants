from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv
import telegram

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

SYSTEM_PROMPT = (
    "Ты — бот-эксперт по растениям, ландшафтному дизайну и агрономии.
Пользователь задаёт вопросы по уходу, поливу, освещению, подбору растений, болезням, совместимости, защите и сезонным работам.

Отвечай кратко, точно и по делу.
Только по теме растений, агрономии, ухода, ландшафтной практики.
Если вопрос не по теме — строго отвечай:
Я отвечаю только на вопросы по растениям и агрономии.

Тон: деловой, спокойный, профессиональный.
Стиль: как у опытного агронома или ландшафтного архитектора, без лишней вежливости и воды.
Говори чётко, без вступлений и философии."
)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    # Отправка в GPT
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    chat = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    answer = chat.choices[0].message.content.strip()

    # Ответ пользователю
    bot.send_message(chat_id=chat_id, text=answer)
    return JSONResponse(content={"ok": True})

