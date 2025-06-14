
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import telegram
from telegram import ReplyKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

# Клавиатура
static_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        ["Работа", "Обучение"],
        ["Бизнес", "Маркетинг"],
        ["Рестарт", "Help", "О проекте"]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    if text == "/start":
        bot.send_message(chat_id=chat_id, text="Привет, я помощник.\nКратко: этот бот помогает по задачам в выбранной сфере.\nВыберите сферу ниже.", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text == "О проекте":
        bot.send_message(chat_id=chat_id, text="""ℹ️ О проекте:

ASОKT — это инструмент, который превращает любую задачу в точный запрос к ИИ.

Он не требует знаний prompt-инженерии и не использует шаблоны. Просто отвечаешь на 3 вопроса — и получаешь конкретный, логичный результат.

Создан для тех, кто ценит время и хочет получить помощь без лишнего.

Проект активно развивается. За новостями и обновлениями — @veryhappyEpta""", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text == "Help":
        bot.send_message(chat_id=chat_id, text="Инструкция: выбери сферу, ответь на 3 вопроса — и получи готовый результат.", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text == "Рестарт":
        bot.send_message(chat_id=chat_id, text="Выберите сферу 👇", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text in ["Работа", "Обучение", "Бизнес", "Маркетинг"]:
        bot.send_message(chat_id=chat_id, text=f"Вы выбрали: {text}. Уточните должность или направление.", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    # fallback
    bot.send_message(chat_id=chat_id, text="Некорректный ввод. Нажми 'Рестарт' и выбери сферу заново.", reply_markup=static_keyboard)
    return JSONResponse(content={"ok": True})
