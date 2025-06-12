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
    "Ты — бот-эксперт по растениям, ландшафту и агрономии. "
    "Пользователь задаёт вопросы: по уходу, поливу, освещению, подбору растений, болезням и т.д. "
    "Отвечай кратко, по делу, только по теме растений и ландшафтной работы. "
    "Если вопрос не по теме — скажи 'Я отвечаю только на вопросы по растениям и агрономии.'"
)

def get_wikidata_description(plant_name):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": plant_name,
        "language": "ru",
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=5).json()
        if r['search']:
            entity_id = r['search'][0]['id']
            summary_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
            summary = requests.get(summary_url, timeout=5).json()
            desc = summary['entities'][entity_id]['descriptions']
            if 'ru' in desc:
                return desc['ru']['value']
            elif 'en' in desc:
                return desc['en']['value']
            else:
                return "Нет описания на русском или английском."
        else:
            return "Нет данных в Wikidata."
    except Exception as e:
        return f"Ошибка Wikidata: {e}"

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

    # Если бот не знает или слишком коротко — добавь Wikidata
    if (
        "я отвечаю только на вопросы по растениям" in gpt_answer.lower()
        or len(gpt_answer) < 20
    ):
        wiki = get_wikidata_description(text)
        answer = f"{gpt_answer}\n\nWikidata: {wiki}"
    else:
        answer = gpt_answer

    bot.send_message(chat_id=chat_id, text=answer)
    return JSONResponse(content={"ok": True})
