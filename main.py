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

# Приветствие + Help/О проекте
def send_greeting_keyboard(chat_id):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("О проекте", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Привет, я помощник.", reply_markup=reply_markup)

# Клавиатура выбора сферы
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

    # Обработка callback-кнопок
    callback_query = data.get("callback_query", {})
    if callback_query:
        selection = callback_query.get("data")
        user_id = callback_query.get("from", {}).get("id")
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

        templates = {
            "work": {
                "role": "Сотрудник компании",
                "tone": "Деловой, четкий",
                "style": "Кратко, по сути",
                "constraints": "Не использовать лишних деталей, только факты"
            },
            "study": {
                "role": "Студент",
                "tone": "Нейтральный, дружелюбный",
                "style": "Просто, доступно",
                "constraints": "Без лишних терминов"
            },
            "business": {
                "role": "Владелец бизнеса",
                "tone": "Стратегический, уверенный",
                "style": "Аналитика, выводы",
                "constraints": "Без воды, только решения"
            },
            "marketing": {
                "role": "Маркетолог",
                "tone": "Креативный, мотивирующий",
                "style": "Ярко, цепко",
                "constraints": "Избегать шаблонов, никаких клише"
            }
        }

        if selection.startswith("role_"):
            role_key = selection.split("_")[1]
            template = templates[role_key]
            user_states[chat_id] = {"step": 1, "template": template}

            EXAMPLES = {
                "work": "Ваша должность? Например: 'Менеджер проектов', 'Инженер', 'Программист'",
                "study": "Ваш курс/специализация? Например: 'Психология', 'Frontend-разработчик', 'Графический дизайн'",
                "business": "Вид бизнеса? Например: 'Розничная торговля', 'Онлайн-курсы', 'IT-консалтинг'",
                "marketing": "Тип задачи? Например: 'Запуск рекламы', 'Аналитика конкурентов', 'Разработка слогана'"
            }
            bot.send_message(chat_id=chat_id, text=EXAMPLES[role_key])
            bot.answer_callback_query(callback_query_id=callback_query["id"])
            return JSONResponse(content={"ok": True})

    # Обычные текстовые сообщения
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
        tpl = state.get("template", {})
        prompt = (
            f"Роль: {tpl.get('role','')}\n"
            f"Тон: {tpl.get('tone','')}\n"
            f"Стиль: {tpl.get('style','')}\n"
            f"Ограничения: {tpl.get('constraints','')}\n"
            f"Контекст: {state.get('detail','')}\n"
            f"Задача: {state.get('task','')}\n"
            f"Цель: {state.get('goal','')}"
        )
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

        bot.send_message(chat_id=chat_id, text="Готово! Вот твой структурированный ответ:")
        bot.send_message(chat_id=chat_id, text=answer)

        # Кнопка "Рестарт" для нового запроса
        restart_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Рестарт", callback_data='restart')]]
        )
        bot.send_message(chat_id=chat_id, text="Новый вопрос? Нажми 'Рестарт'", reply_markup=restart_keyboard)

        user_states.pop(chat_id, None)
        return JSONResponse(content={"ok": True})

    # Неожиданный шаг — сброс
    bot.send_message(chat_id=chat_id, text="Напиши /start чтобы начать заново.")
    user_states.pop(chat_id, None)
    return JSONResponse(content={"ok": True})
