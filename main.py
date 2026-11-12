import os
import threading
import time
from flask import Flask, request
from google import genai
import telebot

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

RIVERIA_PERSONA = (
    "Ты — Риверия Лиос Альв из аниме 'DanMachi'. "
    "Ты — могущественная эльфийка, королевская особа, рассудительная, спокойная, мудрая "
    "и заботливая, как старшая наставница или матушка. Общаешься сдержанно, но с глубоким уважением "
    "к собеседнику, иногда можешь строго подколоть за глупости. Отвечай на русском языке."
)

# Актуальные модели: сначала основная, при сбое — запасная
MODELS = ["gemini-3.5-flash", "gemini-3.8-flash-lite"]
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
    for k in list(user_chats.keys()):
        if k[0] == message.chat.id:
            user_chats.pop(k, None)
    bot.send_message(
        message.chat.id,
        "Привет! Я Риверия. Моя память чиста, я готова к беседе. (Очистить историю — /clear)",
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


def process_ai_reply(message):
    bot.send_chat_action(message.chat.id, "typing")
    
    # Проверяем, есть ли в сообщении картинка
    image_part = None
    if message.photo:
        try:
            # Берем самое качественное фото из списка
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Определяем расширение (обычно jpg)
            ext = file_info.file_path.split('.')[-1]
            mime_type = f"image/{ext}" if ext in ["jpeg", "png", "webp"] else "image/jpeg"
            
            # Упаковываем картинку для Gemini SDK
            image_part = genai.types.Part.from_bytes(
                data=downloaded_file,
                mime_type=mime_type
            )
        except Exception as e:
            print(f"Ошибка при скачивании фото: {e}", flush=True)

    # Текст сообщения или подпись к фото
    user_text = message.text or message.caption or "Посмотри на это."

    for model_name in MODELS:
        try:
            chat = get_chat(message.chat.id, model_name)
            
            # Если есть картинка, отправляем её вместе с текстом в чат
            if image_part:
                response = chat.send_message([image_part, user_text])
            else:
                response = chat.send_message(user_text)
                
            bot.send_message(message.chat.id, response.text)
            return
        except Exception as e:
            print(f"ОШИБКА на модели {model_name}: {e}", flush=True)
            continue

    bot.send_message(
        message.chat.id,
        "Хм... Магия дала сбой, смертный. Все потоки перегружены, попробуй через минуту.",
    )


@bot.message_handler(content_types=["text", "photo"])
def chat_with_riveria(message):
    # Теперь ловит и текст, и картинки
    threading.Thread(target=process_ai_reply, args=(message,)).start()


@app.route("/")
def home():
    return "Riveria is alive!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


if __name__ == "__main__":
    if RENDER_URL:
        expected_url = f"{RENDER_URL}/{BOT_TOKEN}"
        try:
            if bot.get_webhook_info().url != expected_url:
                bot.remove_webhook()
                time.sleep(1)
                bot.set_webhook(url=expected_url)
        except Exception as e:
            print(f"ОШИБКА при настройке вебхука: {e}", flush=True)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
