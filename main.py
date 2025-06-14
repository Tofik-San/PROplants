from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

user_states = {}

# Статичная клавиатура
static_keyboard = ReplyKeyboardMarkup(
    [['Рестарт', 'Help']],
    resize_keyboard=True,
    one_time_keyboard=False
)

def load_prompt_template(role_key):
    file_path = f"prompts/{role_key}.txt"
    print("DEBUG FILE PATH:", file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("ERROR LOADING TEMPLATE:", e)
        return "Роль: Неизвестно\nТон: \nСтиль: \nОграничения: "

def render_prompt(template_text, user_data):
    # user_data = {"detail": ..., "task": ..., "goal": ...}
    try:
        prompt = template_text.format(
            details=user_data.get("detail", ""),
            task=user_data.get("task", ""),
            goal=user_data.get("goal", "")
        )
    except Exception as e:
        print("ERROR RENDER PROMPT:", e)
        prompt = template_text
    print("DEBUG PROMPT:", prompt)
    return prompt

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

    # CALLBACK-КНОПКИ (только выбор сферы)
    callback_query = data.get("callback_query", {})
    if callback_query:
        selection = callback_query.get("data")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")

        if selection.startswith("role_"):
            role_key = selection.split("_")[1]
            print("DEBUG ROLE_KEY:", role_key)
            template_text = load_prompt_template(role_key)
            user_states[chat_id] = {"step": 1, "template": template_text}

            EXAMPLES = {
                "work": "Ваша должность? Например: 'Менеджер проектов', 'Инженер', 'Программист'",
                "study": "Ваш курс/специализация? Например: 'Психология', 'Frontend-разработчик', 'Графический дизайн'",
                "business": "Вид бизнеса? Например: 'Розничная торговля', 'Онлайн-курсы', 'IT-консалтинг'",
                "marketing": "Тип задачи? Например: 'Запуск рекламы', 'Аналитика конкурентов', 'Разработка слогана'"
            }
            bot.send_message(chat_id=chat_id, text=EXAMPLES[role_key], reply_markup=static_keyboard)
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

    # ОБРАБОТКА СООБЩЕНИЙ
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip() if "text" in message else ""

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    state = user_states.get(chat_id, {"step": 0})

    # Старт: приветствие, описание, выбор сферы
    if text.lower() in {"/start", "start"}:
        user_states[chat_id] = {"step": 0}
        bot.send_message(
            chat_id=chat_id,
            text="""👋 Привет! Я — твой AI-помощник ASKT
(Автоматизированный Структурированный Конструктор Твоих задач).

Помогаю решать вопросы — быстро и по делу.
Без промтов, без лишнего текста.

Выбирай сферу, отвечай на 3 вопроса —
и сразу получаешь точный результат.

ℹ Как всё работает — кнопка Help

🚀 Готов? Поехали:""",
            reply_markup=static_keyboard
        )
        send_role_keyboard(chat_id)
        return JSONResponse(content={"ok": True})

    # Рестарт: только выбор сферы (без приветствия)
    if text == "Рестарт":
        user_states[chat_id] = {"step": 0}
        send_role_keyboard(chat_id)
        return JSONResponse(content={"ok": True})

    # Help: просто текст help
    if text == "Help":
        bot.send_message(chat_id=chat_id, text="Help: выбери сферу, ответь на 3 вопроса, получи готовый ответ.", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    step = state.get("step", 0)

    if step == 1 and "detail" not in state:
        state["detail"] = text
        state["step"] = 2
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text="Какую задачу нужно решить?", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if step == 2 and "task" not in state:
        state["task"] = text
        state["step"] = 3
        user_states[chat_id] = state
        bot.send_message(chat_id=chat_id, text="Какой результат хотите получить?", reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if step == 3 and "goal" not in state:
        state["goal"] = text
        template_text = state.get("template", "")

        # Формируем финальный промт с динамической подстановкой
        prompt = render_prompt(template_text, state)

        messages = [
            {
                "role": "system",
                "content": "Ты — эксперт по теме запроса. Дай подробный, конкретный ответ по задаче ниже. Никаких оценок или рекомендаций по формулировке вопроса — только решение по существу."
            },
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

        bot.send_message(chat_id=chat_id, text="Готово! Вот твой структурированный ответ:", reply_markup=static_keyboard)
        bot.send_message(chat_id=chat_id, text=answer, reply_markup=static_keyboard)
        user_states.pop(chat_id, None)
        return JSONResponse(content={"ok": True})

    # Любой неожиданный ввод — сброс и выбор сферы
    bot.send_message(chat_id=chat_id, text="Некорректный ввод. Нажми 'Рестарт' и выбери сферу заново.", reply_markup=static_keyboard)
    user_states.pop(chat_id, None)
    return JSONResponse(content={"ok": True})
