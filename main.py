import os
from flask import Flask, request, render_template_string
from groq import Groq

app = Flask(__name__)

# 初始化 Groq 客戶端（它會自動讀取你在 Render 設定的 GROQ_API_KEY）
client = Groq()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI 台灣學生考卷生成器</title>
    <style>
        body { font-family: "Microsoft JhengHei", Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }
        textarea { width: 100%; height: 180px; padding: 12px; margin: 10px 0; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #007bff; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; border-radius: 4px; font-weight: bold; }
        button:hover { background-color: #0056b3; }
        .result { background: #f8f9fa; border-left: 5px solid #28a745; padding: 20px; margin-top: 20px; white-space: pre-wrap; font-size: 16px; border-radius: 0 4px 4px 0; }
        .hint { color: #666; font-size: 14px; margin-bottom: 5px; }
    </style>
</head>
<body>
    <h2>📝 AI 台灣學生考卷快速生成器</h2>
    <p class="hint">💡 提示：建議把課文、單字清單或具體範圍直接貼在下面，AI 出題會 100% 精準！</p>
    <form method="POST">
        <textarea name="subject" placeholder="範例輸入：
請針對以下【台灣國一歷史課文】出 3 題單選題：
【課文開始】
1624年，荷蘭東印度公司佔領台灣南部，建立熱蘭遮城展開殖民統治。荷蘭人引進王田制度，並大量招募漢人開墾，主要出口鹿皮與砂糖。
【課文結束】"></textarea>
        <button type="submit">🚀 開始生成台灣考卷</button>
    </form>

    {% if exam_content %}
    <h3>✨ 產出的考卷內容：</h3>
    <div class="result">{{ exam_content }}</div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    exam_content = None
    if request.method == 'POST':
        user_input = request.form.get('subject')
        try:
            # 使用 Groq 平台上對繁體中文及結構理解極佳的 llama3-8b 模型
            completion = client.chat.completions.create(
                #  新的正確程式碼
model="llama-3.1-8b-instant",

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位台灣的國民中小學與高級中學教師，完全精通台灣的『108課綱』。 "
                            "請嚴格遵守以下出題規則：\n"
                            "1. 必須完全使用『繁體中文（台灣繁體）』出題，禁止出現任何簡體字。\n"
                            "2. 必須使用台灣當地的教育與生活用語（例如：機率、百分比、硬碟、影印、土豆是指馬鈴薯）。絕不允許使用中國大陸用語。\n"
                            "3. 考卷結構必須清晰，每題包含：題號、題目、(A)(B)(C)(D)四個選項。\n"
                            "4. 在考卷最下方，必須提供『標準答案』與針對台灣學生的『繁體中文詳細解析』。"
                        )
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            )
            exam_content = completion.choices.message.content
        except Exception as e:
            exam_content = f"系統出錯，錯誤訊息：{str(e)}"
            
    return render_template_string(HTML_TEMPLATE, exam_content=exam_content)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
