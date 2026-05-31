import os
from flask import Flask
from google import genai

app = Flask(__name__)

# 初始化 Google AI，它會自動抓取你設定的 GEMINI_API_KEY
client = genai.Client()

# 這裡設定的是「首頁 (/)」，這樣你一打開網址就不會再出現 Not Found 了！
@app.route('/')
def home():
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='你好！請用一句幽默的話跟世界打招呼。',
        )
        return f"<h1>AI 成功回應：</h1><p>{response.text}</p>"
    except Exception as e:
        return f"<h1>連線成功，但 API 出現錯誤：</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
