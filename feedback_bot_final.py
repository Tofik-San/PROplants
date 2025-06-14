
from telebot import TeleBot
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_BOT_TOKEN"
bot = TeleBot(TOKEN)
app = FastAPI()

# Сохраняем ID пользователей, ожидающих фидбек после "dislike"
disliked_users = set()

@app.post("/")
async def webhook(request: Request):
    update = bot.types.Update.de_json(await request.json())
    bot.process_new_updates([update])
    return JSONResponse(content={"ok": True})

@bot.message_handler(commands=['start'])
def handle_start(message):
    payload = message.text.split(' ', 1)[-1] if ' ' in message.text else None

    if payload == 'like':
        bot.send_message(message.chat.id, "Спасибо за положительный отзыв! 🙌")
    elif payload == 'dislike':
        disliked_users.add(message.from_user.id)
        bot.send_message(message.chat.id, "Спасибо за оценку. Напишите, что именно не устроило.")
    else:
        bot.send_message(message.chat.id, "Привет! Оставь свой отзыв о работе ASKT.")

@bot.message_handler(func=lambda message: True)
def handle_feedback(message):
    if message.from_user.id in disliked_users:
        disliked_users.remove(message.from_user.id)
        return  # Молча пропускаем сообщение
    # остальные сообщения бот может игнорировать или обработать

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("feedback_bot_final:app", host="0.0.0.0", port=8000)
