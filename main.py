from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv
import telegram
import requests

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

SYSTEM_PROMPT = (
    "Ты — бот-эксперт по растениям, ландшафтному дизайну и агрономии. "
    "Пользователь задаёт вопросы: по уходу, поливу, освещению, подбору растений, болезням и т.д. "
    "Отвечай кратко, по делу, только по теме растений и ландшафтной работы. "
    "Если вопрос не по теме — скажи 'Я отвечаю только на вопросы по растениям и агрономии.'"
)

def get_wikidata_description(query):
    url = (
        "https://www.wikidata.org/w/api.php"
        "?action=wbsearchentities&format=json&language=ru&type=item&search=" + query
    )
    r = requests.get(url)
    results = r.json().get("search", [])
    if not results:
        return ""
    entity_id = results[0]["id"]
    desc_url = (
        "https://www.wikidata.org/w/api.php"
        "?action=wbgetentities&format=json&languages=ru&ids=" + entity_id
    )
    desc_r = requests.get(desc_url)
    entity = desc_r.json().get("entities", {}).get(entity_id, {})
    description = entity.get("descriptions", {}).get("ru", {}).get("value", "")
    return description

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    chat = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    gpt_answer = chat.choices[0].message.content.strip()

    # Если ответ короткий или "не знаю" — дополняем парсингом
    if (
        "я отвечаю только на вопросы по растениям" in gpt_answer.lower()
        or len(gpt_answer) < 20
    ):
        desc = get_wikidata_description(text)
        if desc:
            answer = f"{gpt_answer}\n{desc}"
        else:
            answer = gpt_answer
    else:
        answer = gpt_answer

    bot.send_message(chat_id=chat_id, text=answer)
    return JSONResponse(content={"ok": True})
