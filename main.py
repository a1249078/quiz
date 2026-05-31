import os
from flask import Flask, request, render_template_string
from groq import Groq

app = Flask(__name__)

# 初始化 Groq 客戶端（自動讀取 Render 設定的 GROQ_API_KEY）
client = Groq()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI 台灣學生考卷生成器</title>
    <style>
        body { font-family: "Microsoft JhengHei", Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }
        .nav-links { background: #f1f3f5; padding: 10px 15px; border-radius: 4px; margin-bottom: 20px; }
        .nav-links a { color: #007bff; text-decoration: none; font-weight: bold; margin-right: 15px; }
        .nav-links a:hover { text-decoration: underline; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input[type="text"], input[type="number"] { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        button { background-color: #28a745; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; border-radius: 4px; font-weight: bold; width: 100%; margin-top: 10px; }
        button:hover { background-color: #218838; }
        .result { background: #f8f9fa; border-left: 5px solid #007bff; padding: 20px; margin-top: 20px; white-space: pre-wrap; font-size: 16px; border-radius: 0 4px 4px 0; }
    </style>
</head>
<body>

    <!-- 🌐 首頁導覽超連結 -->
    <div class="nav-links">
        <a href="/">🏠 首頁：考卷生成器</a>
    </div>

    <h2>📝 AI 台灣學生考卷快速生成器</h2>
    
    <form method="POST">
        <div class="row">
            <div class="col form-group">
                <label>1️⃣ 學生年級</label>
                <input type="text" name="grade" placeholder="例如：國中一年級、國小五年級" required>
            </div>
            <div class="col form-group">
                <label>2️⃣ 考試科目 / 具體範圍</label>
                <input type="text" name="subject" placeholder="例如：數學（二元一次方程式）、英文單字" required>
            </div>
        </div>

        <div class="row">
            <div class="col form-group">
                <label>3️⃣ 選擇題數量 (題)</label>
                <input type="number" name="num_choice" min="0" placeholder="沒寫則不加入此題型">
            </div>
            <div class="col form-group">
                <label>4️⃣ 填充題數量 (題)</label>
                <input type="number" name="num_blank" min="0" placeholder="沒寫則不加入此題型">
            </div>
            <div class="col form-group">
                <label>5️⃣ 計算/問答題數量 (題)</label>
                <input type="number" name="num_calc" min="0" placeholder="沒寫則不加入此題型">
            </div>
        </div>

        <button type="submit">🚀 依條件生成台灣考卷</button>
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
        # 讀取表單中 5 個框框的內容
        grade = request.form.get('grade', '').strip()
        subject = request.form.get('subject', '').strip()
        num_choice = request.form.get('num_choice', '').strip()
        num_blank = request.form.get('num_blank', '').strip()
        num_calc = request.form.get('num_calc', '').strip()

        # 動態建立題型要求，沒填或填 0 就跳過
        question_requirements = []
        if num_choice and int(num_choice) > 0:
            question_requirements.append(f"- 選擇題：共 {num_choice} 題 (每題皆須附上 A, B, C, D 四個選項)")
        if num_blank and int(num_blank) > 0:
            question_requirements.append(f"- 填充題：共 {num_blank} 題")
        if num_calc and int(num_calc) > 0:
            question_requirements.append(f"- 計算/問答題：共 {num_calc} 題")

        # 如果老師什麼題型數量都沒填，給予預設提示
        if not question_requirements:
            exam_content = "錯誤提示：請至少在選擇題、填充題或計算題其中一個框框中輸入大於 0 的數量。"
            return render_template_string(HTML_TEMPLATE, exam_content=exam_content)

        # 組合出高度客製化的出題提示詞 (Prompt)
        requirements_str = "\n".join(question_requirements)
        user_prompt = (
            f"請幫我針對【{grade}】的【{subject}】科目出題。\n"
            f"考卷中必須包含且只能包含以下題型及數量，其餘沒提到的題型請完全跳過：\n"
            f"{requirements_str}"
        )

        try:
            # 呼叫 Groq 最新世代 8B 瞬時模型
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位台灣的國民中小學與高級中學教師，完全精通台灣的『108課綱』。 "
                            "請嚴格遵守以下出題規則：\n"
                            "1. 必須完全使用『繁體中文（台灣繁體）』出題，禁止出現任何簡體字。\n"
                            "2. 必須使用台灣當地的教育與生活用語（例如：機率、百分比、硬碟、影印、土豆是指馬鈴薯）。絕不允許使用中國大陸用語。\n"
                            "3. 考卷結構必須清晰，每種題型的大標題要分明。\n"
                            "4. 在考卷最下方，必須提供與題目順序對應的『標準答案』與針對台灣學生的『繁體中文詳細解析』。"
                        )
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            exam_content = completion.choices[0].message.content
        except Exception as e:
            exam_content = f"系統出錯，錯誤訊息：{str(e)}"
            
    return render_template_string(HTML_TEMPLATE, exam_content=exam_content)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
