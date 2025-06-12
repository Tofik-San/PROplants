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
    "Отвечай только на вопросы по растениям, агрономии, уходу, болезням, подбору. "
    "Не используй приветствия, обращения, извинения и вводные фразы. Только факт, коротко, строго по теме."
)

BLOCKED_COMMANDS = {"/start", "start", "привет", "hello", "hi"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    # Блокируем приветствия и пустые запросы
    if text.lower() in BLOCKED_COMMANDS:
        bot.send_message(chat_id=chat_id, text="Задай вопрос по растениям или агрономии.")
        return JSONResponse(content={"ok": True})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    chat = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    answer = chat.choices[0].message.content.strip()

    bot.send_message(chat_id=chat_id, text=answer)
    return JSONResponse(content={"ok": True})
