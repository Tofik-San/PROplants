from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

user_states = {}

# === ФУНКЦИЯ ЗАГРУЗКИ ФАЙЛОВОГО ПРОМТА ===
def load_prompt_template(role_key):
    file_path = f"prompts/{role_key}.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "Роль: Неизвестно\nТон: \nСтиль: \nОграничения: "

# === КНОПКИ ===
def send_greeting_keyboard(chat_id):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("О проекте", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Привет, я помощник.", reply_markup=reply_markup)

def send_role_keyboard(chat_id):
    keyboard = [
        [
            InlineKeyboardButton("Работа", callback_data='role_work'),
            InlineKeyboardButton("Обучение", callback_data='role_study')
        ],
        [
            InlineKeyboardButton("Бизнес", callback_data='role_business'),
            InlineKeyboardButton("Маркетинг", callback_data='role_marketing')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Выберите сферу:", reply_markup=reply_markup)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    # === CALLBACK-КНОПКИ ===
    callback_query = data.get("callback_query", {})
    if callback_query:
        selection = callback_query.get("data")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")

        if selection == "help":
            bot.send_message(chat_id=chat_id, text="Сейчас покажу как это работает")
            send_role_keyboard(chat_id)
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

        if selection == "about":
            bot.send_message(chat_id=chat_id, text="Помогаю с задачами")
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

        if selection == "restart":
            user_states[chat_id] = {"step": 0}
            send_greeting_keyboard(chat_id)
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

        # === Внешние шаблоны ===
        if selection.startswith("role_"):
            role_key = selection.split("_")[1]
            template_text = load_prompt_template(role_key)
            user_states[chat_id] = {"step": 1, "template": template_text}

            EXAMPLES = {
                "work": "Ваша должность? Например: 'Менеджер проектов', 'Инженер', 'Программист'",
                "study": "Ваш курс/специализация? Например: 'Психология', 'Frontend-разработчик', 'Графический дизайн'",
                "business": "Вид бизнеса? Например: 'Розничная торговля', 'Онлайн-курсы', 'IT-консалтинг'",
                "marketing": "Тип задачи? Например: 'Запуск рекламы', 'Аналитика конкурентов', 'Разработка слогана'"
            }
            bot.send_message(chat_id=chat_id, text=EXAMPLES[role_key])
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

    # === ОБРАБОТКА СООБЩЕНИЙ ===
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip() if "text" in message else ""

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    state = user_states.get(chat_id, {"step": 0})

    if text.lower() in {"/start", "start"}:
        user_states[chat_id] = {"step": 0}
        send_greeting_keyboard(chat_id)
        return JSONResponse(content={"ok": True})

    step = state.get("step", 0)

    if step == 1 and "detail" not in state:
        state["detail"] = text
        state["step"] = 2
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text="Какую задачу нужно решить?")
        return JSONResponse(content={"ok": True})

    if step == 2 and "task" not in state:
        state["task"] = text
        state["step"] = 3
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text="Какой результат хотите получить?")
        return JSONResponse(content={"ok": True})

    if step == 3 and "goal" not in state:
        state["goal"] = text
        template_text = state.get("template", "")
        additions = (
            f"\nКонтекст: {state.get('detail','')}\n"
            f"Задача: {state.get('task','')}\n"
            f"Цель: {state.get('goal','')}"
        )
        prompt = template_text + additions

        messages = [
            {"role": "system", "content": "Ты — эксперт по теме запроса. Дай подробный, конкретный ответ по задаче ниже. Никаких оценок или рекомендаций по формулировке вопроса — только решение по существу."},
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

        bot.send_message(chat_id=chat_id, text="Готово! Вот что можно предпринять:")
        bot.send_message(chat_id=chat_id, text=answer)

        # Кнопка "Рестарт"
        restart_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Рестарт", callback_data='restart')]]
        )
        bot.send_message(chat_id=chat_id, text="Новый вопрос? Нажми 'Рестарт'", reply_markup=restart_keyboard)

        user_states.pop(chat_id, None)
        return JSONResponse(content={"ok": True})

    # Любой неожиданный ввод — сброс
    bot.send_message(chat_id=chat_id, text="Напиши /start чтобы начать заново.")
    user_states.pop(chat_id, None)
    return JSONResponse(content={"ok": True})
