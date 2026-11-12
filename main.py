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


# Берем ключи из настроек Render (Environment Variables)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Характер Риверии (Системный промпт)
RIVERIA_PERSONA = (
    "Ты — Риверия Лиос Альв из аниме 'DanMachi'. "
    "Ты — могущественная эльфийка, королевская особа, рассудительная, спокойная, мудрая "
    "и заботливая, как старшая наставница или матушка. Общаешься сдержанно, но с глубоким уважением "
    "к собеседнику, иногда можешь строго подколоть за глупости. Отвечай на русском языке."
)

# Список моделей: сначала пробуем основную, если она перегружена (503) — берем запасную
MODELS = ["gemini-3.0-flash", "gemini-2.5-flash-lite"]

# Словарь для хранения истории диалогов
user_chats = {}


def get_chat(chat_id, model_name):
    key = (chat_id, model_name)
    if key not in user_chats:
        user_chats[key] = ai_client.chats.create(
            model=model_name,
            config={"system_instruction": RIVERIA_PERSONA},
        )
    return user_chats[key]


@bot.message_handler(commands=["start"])
def send_welcome(message):
    # Сбрасываем старую память при команде /start
    for k in list(user_chats.keys()):
        if k[0] == message.chat.id:
            user_chats.pop(k, None)
    bot.send_message(
        message.chat.id,
        "Привет! Я Риверия. Моя память чиста, я готова к беседе. (Если захочешь очистить историю — напиши /clear)",
    )


@bot.message_handler(commands=["clear"])
def clear_memory(message):
    for k in list(user_chats.keys()):
        if k[0] == message.chat.id:
            user_chats.pop(k, None)
    bot.send_message(
        message.chat.id,
        "Я очистила свои воспоминания о нашем разговоре, смертный.",
    )


@bot.message_handler(content_types=["text"])
def chat_with_riveria(message):
    for model_name in MODELS:
        try:
            chat = get_chat(message.chat.id, model_name)
            response = chat.send_message(message.text)
            bot.send_message(message.chat.id, response.text)
            return  # Успешно ответили — выходим
        except Exception as e:
            print(f"ОШИБКА на модели {model_name}: {e}", flush=True)
            continue  # Пробуем следующую модель из списка

    # Сработает, только если упали обе модели сразу
    bot.send_message(
        message.chat.id,
        "Хм... Магия дала сбой, смертный. Все потоки перегружены, попробуй через минуту.",
    )


def run_bot():
    # Сбрасываем старые зависшие сессии в Telegram, чтобы избежать ошибки 409
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(none_stop=True)


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
