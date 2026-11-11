from flask import Flask
import threading
import telebot
from google import genai

app = Flask(__name__)

@app.route('/')
def home():
    return "Riveria is alive!"

# Инициализируем бота
bot = telebot.TeleBot("9054518979:AAHXED4Dlbv1JbVj1sL-CHRfS2ajfmZL9Bc")
ai_client = genai.Client(api_key="AQ.Ab8RN6iA5AVPx6wIxQ2AZCp6wixQ2AZCp")

# Здесь твой остальной код с хендлерами и логикой Риверии...

def run_bot():
    # Запускаем бесконечный опрос телеграма в фоне
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем телеграм-бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # А сам Flask запускаем на главном потоке, чтобы он сразу занял порт 10000 для Render
    app.run(host='0.0.0.0', port=10000)

import telebot
from google import genai

# Инициализируем твоего бота и клиента ИИ
bot = telebot.TeleBot("9054518979:AAHXED4Dlbv1JbVj1sL-CHRfS2ajfmZL9Bc")
ai_client = genai.Client(api_key="AQ.Ab8RN6IA5AVPcxGwiXQ2AZCpe2QXgUZ0mZtiL7in-SMsM1dgGA")

# Характер Риверии (Системный промпт)
RIVERIA_PERSONA = (
    "Ты — Риверия Лиос Альв из аниме 'DanMachi'. "
    "Ты — могущественная эльфийка, королевская особа, рассудительная, спокойная, мудрая "
    "и заботливая, как старшая наставница или матушка. Общаешься сдержанно, но с глубоким уважением "
    "к собеседнику, иногда можешь строго подколоть за глупости. Отвечай на русском языке."
)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я Риверия, твой личный бот. Все работает!")

# Обработка всех остальных текстовых сообщений через ИИ
@bot.message_handler(func=lambda message: True)
def chat_with_riveria(message):
    try:
        # Отправляем сообщение пользователя нейросети вместе с характером Риверии
        response = ai_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=message.text,
            config=
            { 'system_instruction': RIVERIA_PERSONA
              }
        )


        # Отправляем ответ Риверии обратно в чат
        bot.send_message(message.chat.id, response.text)
    except Exception as e:
        print(f"ОШИБКА: {e}")
        bot.send_message(message.chat.id, "Хм... Магия дала сбой, смертный. Попробуй еще раз.")

bot.polling(none_stop=True)



