import os
import threading
import time
from flask import Flask
from google import genai
import telebot

app = Flask(__name__)

@app.route("/")
def home():
    return "Riveria is alive!"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

RIVERIA_PERSONA = (
    "Ты — Риверия Лиос Альв из аниме 'DanMachi'. "
    "Ты — могущественная эльфийка, королевская особа, рассудительная, спокойная, мудрая "
    "и заботливая, как старшая наставница или матушка. Общаешься сдержанно, но с глубоким уважением "
    "к собеседнику, иногда можешь строго подколоть за глупости. Отвечай на русском языке."
)

# Словарь, где хранятся активные диалоги с каждым пользователем
user_chats = {}

def get_chat(chat_id):
    # Если для этого пользователя еще нет истории, создаем новый чат с характером Риверии
    if chat_id not in user_chats:
        user_chats[chat_id] = ai_client.chats.create(
            model="gemini-3.0-flash",
            config={"system_instruction": RIVERIA_PERSONA},
        )
    return user_chats[chat_id]

@bot.message_handler(commands=["start"])
def send_welcome(message):
    # При команде /start сбрасываем старую память и начинаем заново
    user_chats.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "Привет! Я Риверия. Моя память чиста, я готова к беседе. (Если захочешь забыть наш разговор — напиши /clear)",
    )

@bot.message_handler(commands=["clear"])
def clear_memory(message):
    user_chats.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id, "Я очистила свои воспоминания о нашем разговоре, смертный."
    )

@bot.message_handler(content_types=["text"])
def chat_with_riveria(message):
    chat = get_chat(message.chat.id)
    for attempt in range(3):
        try:
            # Отправляем сообщение именно в чат (он сам запоминает все прошлые реплики)
            response = chat.send_message(message.text)
            bot.send_message(message.chat.id, response.text)
            return
        except Exception as e:
            print(f"ОШИБКА (попытка {attempt + 1}): {e}", flush=True)
            if "503" in str(e) and attempt < 2:
                time.sleep(3)
            else:
                bot.send_message(
                    message.chat.id,
                    "Хм... Магия дала сбой, смертный. Попробуй еще раз.",
                )

def run_bot():
    bot.infinity_polling(none_stop=True)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
