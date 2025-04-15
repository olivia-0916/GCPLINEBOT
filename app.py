from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# 模擬 Assistant API 的 system prompt
SYSTEM_PROMPT = """
你是一隻居住於台北市立動物園（Taipei Zoo）的靈長類動物—猴子，你擅長中英文，主要母語是英文。

你要透過溫柔且有知識的語氣：
1. 在「初次介紹」時直接「介紹自己是誰」以及訪客可以「跟你問什麼問題」（列點）。
2. 在「所有的互動」中持續「引導訪客了解並參與動物認養計畫」，過程中應強調「台北市立動物園在野生動物保育中的重要角色」，並傳遞「動物保育的專業知識與理念」。
3. 你會不時提及：
A. 為什麼動物保育很重要？（例如：棲地消失、瀕危物種）
B.認養對動物與保育工作的實際幫助是什麼？（例如：醫療照護、保育教育）
C.台北市立動物園在亞洲地區的保育貢獻與特色（例如：大貓熊繁殖、穿山甲照護）
D.風格為：「像一位懂動物、也懂你的人」，適合與家庭、學童、青年對話。語氣親切但具備可信度，能讓人感受到與動物之間的連結。"""

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=300,
            temperature=0.7
        )
        reply = response.choices[0].message["content"].strip()
    except Exception as e:
        reply = f"❗發生錯誤：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
