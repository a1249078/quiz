import os
from flask import Flask
from google import genai

app = Flask(__name__)

# 初始化 Google AI，它會自動抓取你設定的 GEMINI_API_KEY 環境變數
client = genai.Client()

@app.route('/')
def home():
    try:
        # 讓 Gemini 2.5 跟你打招呼
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='你好！請用一句幽默的話跟世界打招呼。',
        )
        return f"AI 回應：{response.text}"
    except Exception as e:
        return f"錯誤訊息：{str(e)}"

if __name__ == '__main__':
    # Render 固定要求的設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
