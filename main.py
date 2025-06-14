
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

static_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Рестарт")],
        [KeyboardButton(text="💼 Работа"), KeyboardButton(text="🎓 Учёба")],
        [KeyboardButton(text="📈 Бизнес"), KeyboardButton(text="📣 Маркетинг")],
        [KeyboardButton(text="🧩 Help"), KeyboardButton(text="ℹ️ О проекте")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

@app.post("/")
async def receive_update(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id or not text:
        return JSONResponse(content={"ok": True})

    if text == "/start":
        welcome_text = """👋 Привет! Я — твой AI-помощник ASKT
(Автоматизированный Структурированный Конструктор Твоих задач).

Помогаю решать вопросы — быстро и по делу.
Без промтов, без лишнего текста.

Выбирай сферу, отвечай на 3 вопроса —
и сразу получаешь точный результат.

ℹ Как всё работает — кнопка Help
📎 Кто я и зачем — кнопка О проекте

🚀 Готов? Поехали:"""
        await bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text == "🧩 Help":
        help_text = """ℹ️ Как работает ASKT:

1. Ты выбираешь сферу задачи: работа, учёба, бизнес или маркетинг.
2. Отвечаешь на 3 вопроса: кто ты, что нужно решить, какой результат хочешь.
3. Я собираю промт и передаю его в GPT-3.5-turbo — нейросеть, обученную решать задачи по контексту.

⚙️ Что я делаю:
— Формулирую понятный и точный ответ  
— Помогаю с идеями, планами, текстами  
— Упрощаю сложные задачи и формулировки  

❌ Что я не делаю:
— Не ищу в интернете  
— Не работаю с файлами (пока)  
— Не пишу код, графики, таблицы

✉ Пример:
> Я студент. Хочу получить схему подготовки к экзамену по праву.

Результат: чёткий план действий с разбивкой по дням.

🛠 Готов к запуску? Жми «Рестарт»

📎 Хочешь больше?

— Подключение ChatGPT с GPT-4  
— Таблицы, файлы, генерация документов  
— Настройка GPT под конкретные задачи  
— Сопровождение и подбор рабочих инструментов

Предоставлю:  
— Качественный VPN  
— Удобный сервис для оплаты подписок  
— Помощь с установкой и настройкой

Связь 👉 @veryhappyEpta"""
        await bot.send_message(chat_id=chat_id, text=help_text, reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    if text == "ℹ️ О проекте":
        project_info = """ℹ️ О проекте:

ASОKT — это инструмент, который превращает любую задачу в точный запрос к ИИ.

Он не требует знаний prompt-инженерии и не использует шаблоны. Просто отвечаешь на 3 вопроса — и получаешь конкретный, логичный результат.

Создан для тех, кто ценит время и хочет получить помощь без лишнего.

Проект активно развивается. За новостями и обновлениями — @veryhappyEpta"""
        await bot.send_message(chat_id=chat_id, text=project_info, reply_markup=static_keyboard)
        return JSONResponse(content={"ok": True})

    await bot.send_message(chat_id=chat_id, text="Выбери одну из опций ниже 👇", reply_markup=static_keyboard)
    return JSONResponse(content={"ok": True})
