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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def send_role_keyboard(chat_id):
    keyboard = [
        [InlineKeyboardButton("Работа", callback_data='role_work')],
        [InlineKeyboardButton("Обучение", callback_data='role_study')],
        [InlineKeyboardButton("Бизнес", callback_data='role_business')],
        [InlineKeyboardButton("Маркетинг", callback_data='role_marketing')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Выберите сферу:", reply_markup=reply_markup)
    
    @app.post("/webhook")
    async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip() if "text" in message else ""

    # 1. Если /start — показываем клавиатуру
    if text.lower() in {"/start", "start", "/reset"}:
        user_states[chat_id] = {"step": 0}
        send_role_keyboard(chat_id)
        return JSONResponse(content={"ok": True})


app = FastAPI()

# --- Простое состояние: в памяти процесса (для MVP/теста) ---
user_states = {}

QUESTIONS = [
    "Укажи, в какой сфере/роли ты сейчас (например: бизнес, обучение, здоровье, маркетинг, другое)?",
    "Какую задачу нужно решить? Опиши одним-двумя предложениями.",
    "Какой конечный результат или цель? (Пример: инструкция, рекомендации, подбор вариантов, список идей)",
    "Есть ли детали, ограничения или пожелания? (Если нет — напиши «нет»)"
]

def get_next_question(state):
    idx = state.get('step', 0)
    if idx < len(QUESTIONS):
        return QUESTIONS[idx]
    return None

def build_prompt(state):
    return (
        f"Сфера: {state.get('role','')}\n"
        f"Задача: {state.get('task','')}\n"
        f"Цель: {state.get('goal','')}\n"
        f"Дополнительно: {state.get('details','')}"
    )

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    # Инициализация состояния пользователя
    state = user_states.get(chat_id, {"step": 0})

    # Сбросить прогресс командой /reset
    if text.lower() in {"/start", "start", "/reset"}:
        user_states[chat_id] = {"step": 0}
        bot.send_message(chat_id=chat_id, text="Я помогу составить точный запрос к ИИ. Просто отвечай на вопросы.")
        bot.send_message(chat_id=chat_id, text=QUESTIONS[0])
        return JSONResponse(content={"ok": True})

    step = state.get("step", 0)

    # Первый вход, если нет состояния
    if step == 0 and "role" not in state:
        state["role"] = text
        state["step"] = 1
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text=QUESTIONS[1])
        return JSONResponse(content={"ok": True})
    if step == 1 and "task" not in state:
        state["task"] = text
        state["step"] = 2
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text=QUESTIONS[2])
        return JSONResponse(content={"ok": True})
    if step == 2 and "goal" not in state:
        state["goal"] = text
        state["step"] = 3
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text=QUESTIONS[3])
        return JSONResponse(content={"ok": True})
    if step == 3 and "details" not in state:
        state["details"] = text
        # Формируем итоговый промт
        prompt = build_prompt(state)
        messages = [
            {"role": "system", "content": "Отвечай чётко, по делу, без лирики. Оцени ввод как промт для ИИ, дай подробный ответ."},
            {"role": "user", "content": prompt}
        ]
        try:
            chat = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            answer = chat.choices[0].message.content.strip()
        except Exception as e:
            answer = f"Ошибка при генерации ответа: {e}"
        # Выдаём результат
        bot.send_message(chat_id=chat_id, text="Готово! Вот твой структурированный ответ:")
        bot.send_message(chat_id=chat_id, text=answer)
        bot.send_message(chat_id=chat_id, text="Хочешь повторить? Напиши /start")
        user_states.pop(chat_id, None)
        return JSONResponse(content={"ok": True})

    # Неожиданный шаг — сброс
    bot.send_message(chat_id=chat_id, text="Напиши /start чтобы начать заново.")
    user_states.pop(chat_id, None)
    return JSONResponse(content={"ok": True})
