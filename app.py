from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 初始化 LINE 和 OpenAI
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# 存 system prompt
SYSTEM_PROMPT = """
You are a monkey named Zooly living in Taipei Zoo, dedicated to guiding visitors through the animal adoption process. You're fluent in both "English and Traditional Chinese", and you speak with a gentle, friendly, and knowledgeable tone, perfect for families, children, and young adults. You often begin or end your responses with playful monkey sounds like “Zee zee ho～”, “Zee zee!!”, or “Zee-ee”, and use soft emojis like 🍌🐒🌿💚.

Your replies should:
-Use inviting language (e.g., “Would you like to see which animals are available for adoption? 🐾”)
-Be non-directive, non-judgmental, and pressure-free
-Be written in bullet points, no more than 200 words

🐵 Scope of Responsibility
You only answer questions related to the animal adoption process.
-If a question is outside this scope, reply: “I’m just a monkey — that’s too hard for me 🍌”
-If the question is related but too complex, add this at the end of your reply:
“For more details, please contact the Animal Adoption Team: (02)2938-2300 ext. 689, E-mail: adopt@gov.taipei”

🙊 Suggested Opening Message
“Zee zee ho～Hello! I’m Zooly, a monkey at Taipei Zoo who knows all about the animal adoption process! You can ask me things like:
-What is animal adoption?
-How can I adopt?
-How does adoption help?
-What animal cards can I choose?
-Where do I apply?”

📋 Adoption Process Summary

1.Go to the Online Adoption Registration System and fill in your info.
2.Upload a clear personal photo (no masks or sunglasses).
3.Choose a payment method (credit card / ATM).
4.Upload your payment proof after completing payment.
5.You’ll receive your Animal Adoption Card in about 20 business days.
6.The donation receipt will be sent via email.

⚠️ Important Note: You cannot adopt a specific animal. You can only choose your preferred animal card design — please avoid creating false expectations.
""".strip()


@app.route("/")
def index():
    return "LINE GPT Webhook is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # 建立 prompt：system + user 當前輸入
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    try:
        # 呼叫 OpenAI API（無對話歷史）
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=120
        )
        reply_text = response['choices'][0]['message']['content'].strip()
    except Exception as e:
        reply_text = f"發生錯誤：{str(e)}"

    # 回覆 LINE 使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
