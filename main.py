import os
import json
from flask import Flask, request, render_template_string
from groq import Groq

app = Flask(__name__)

# 初始化 Groq 客戶端
client = Groq()

cached_questions = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI 台灣學生線上考卷生成器</title>
    <style>
        body { font-family: "Microsoft JhengHei", Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 0 20px; line-height: 1.6; color: #333; background-color: #fcfcfc; }
        .setup-box { background: #ffffff; border: 1px solid #e0e0e0; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 30px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #444; }
        input[type="text"], input[type="number"] { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        .btn-generate { background-color: #007bff; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; border-radius: 4px; font-weight: bold; width: 100%; margin-top: 10px; }
        .btn-generate:hover { background-color: #0056b3; }
        .exam-area { background: #ffffff; border: 1px solid #dee2e6; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .q-card { background: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; margin-bottom: 20px; border-radius: 6px; }
        .q-title { font-weight: bold; font-size: 18px; margin-bottom: 12px; color: #222; }
        .option-lbl { display: block; margin: 10px 0; cursor: pointer; padding: 5px; border-radius: 4px; }
        .option-lbl:hover { background-color: #e9ecef; }
        .txt-input { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .btn-submit { background-color: #28a745; color: white; border: none; padding: 12px 40px; font-size: 18px; cursor: pointer; border-radius: 4px; font-weight: bold; display: block; margin: 20px auto 0 auto; }
        .btn-submit:hover { background-color: #218838; }
        .score-board { text-align: center; background: #fff3cd; border: 2px dashed #ffc107; padding: 20px; border-radius: 8px; margin-bottom: 25px; }
        .score { font-size: 48px; color: #dc3545; font-weight: bold; }
        .report-card { border: 1px solid #dee2e6; padding: 15px; margin-bottom: 15px; border-radius: 6px; }
        .correct { border-left: 5px solid #28a745; background: #f4faf5; }
        .wrong { border-left: 5px solid #dc3545; background: #fff5f5; }
        .analysis { background: #e9ecef; padding: 10px; font-size: 14px; margin-top: 10px; border-radius: 4px; color: #555; }
        .error { color: #dc3545; font-weight: bold; background: #ffebeb; padding: 10px; border-radius: 4px; }
    </style>
</head>
<body>

    <div class="setup-box">
        <h3 style="margin-top:0;">📝 AI 台灣學生考卷設定 (大題量優化版)</h3>
        <form method="POST" action="/generate">
            <div class="row">
                <div class="col form-group">
                    <label>1️⃣ 學生年級</label>
                    <input type="text" name="grade" placeholder="例如：國中一年級" required>
                </div>
                <div class="col form-group">
                    <label>2️⃣ 考試科目 / 範圍</label>
                    <input type="text" name="subject" placeholder="例如：歷史（荷西時期）" required>
                </div>
            </div>
            <div class="row">
                <div class="col form-group">
                    <label>3️⃣ 選擇題數量</label>
                    <input type="number" name="num_choice" min="0" placeholder="可出高達 30~40 題">
                </div>
                <div class="col form-group">
                    <label>4️⃣ 填充題數量</label>
                    <input type="number" name="num_blank" min="0" placeholder="沒寫或填0則跳過">
                </div>
                <div class="col form-group">
                    <label>5️⃣ 計算題數量</label>
                    <input type="number" name="num_calc" min="0" placeholder="沒寫或填0則跳過">
                </div>
            </div>
            <button type="submit" class="btn-generate">🚀 立即在下方生成大量考卷</button>
        </form>
    </div>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

    {% if questions %}
    <div class="exam-area">
        <h3 style="margin-top:0; border-bottom: 2px solid #007bff; padding-bottom: 8px;">✏️ 線上測驗開始（總共 {{ questions|length }} 題，請在下方答題）</h3>
        <form action="/submit" method="POST">
            {% for q in questions %}
            <div class="q-card">
                <div class="q-title">{{ loop.index }}. 〖{{ "選擇題" if q.type == "choice" else "填充題" if q.type == "blank" else "計算/問答題" }}〗{{ q.question }}</div>
                
                {% if q.type == "choice" %}
                    {% for opt in q.options %}
                    <label class="option-lbl">
                        <input type="radio" name="q_{{ q.id }}" value="{{ opt }}" required> {{ opt }}
                    </label>
                    {% endfor %}
                {% elif q.type == "blank" %}
                    <input type="text" name="q_{{ q.id }}" class="txt-input" placeholder="請在此處輸入答案" required>
                {% else %}
                    <textarea name="q_{{ q.id }}" class="txt-input" rows="3" placeholder="請寫出你的計算過程或答案說明" required></textarea>
                {% endif %}
            </div>
            {% endfor %}
            <button type="submit" class="btn-submit">💯 答題完畢，直接線上交卷</button>
        </form>
    </div>
    {% endif %}

    {% if score is not none %}
    <div class="exam-area" style="margin-top: 20px;">
        <div class="score-board">
            <h2>📊 測驗批改報告</h2>
            <div>得分</div>
            <div class="score">{{ score }} / 100 分</div>
        </div>
        <h3>🔍 題目解析與對錯：</h3>
        {% for r in results %}
        <div class="report-card {{ 'correct' if r.is_correct else 'wrong' if r.type != 'calc' else '' }}" style="border-left: 5px solid {% if r.type == 'calc' %}#6c757d{% elif r.is_correct %}#28a745{% else %}#dc3545{% endif %};">
            <strong>第 {{ loop.index }} 題：{{ r.question }}</strong><br>
            ✍️ 您的答案：<span style="font-weight: bold;">{{ r.user_ans }}</span><br>
            {% if r.type != 'calc' and not r.is_correct %}
                ✅ 正確答案：<span style="color: #28a745; font-weight: bold;">{{ r.correct_ans }}</span><br>
            {% endif %}
            <div class="analysis">💡 <b>解析：</b>{{ r.analysis }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, questions=None, score=None, error=None)

@app.route('/generate', methods=['POST'])
def generate_quiz():
    global cached_questions
    grade = request.form.get('grade', '').strip()
    subject = request.form.get('subject', '').strip()
    num_choice = request.form.get('num_choice', '').strip()
    num_blank = request.form.get('num_blank', '').strip()
    num_calc = request.form.get('num_calc', '').strip()

    num_choice = int(num_choice) if num_choice and int(num_choice) > 0 else 0
    num_blank = int(num_blank) if num_blank and int(num_blank) > 0 else 0
    num_calc = int(num_calc) if num_calc and int(num_calc) > 0 else 0

    if num_choice == 0 and num_blank == 0 and num_calc == 0:
        return render_template_string(HTML_TEMPLATE, questions=None, score=None, error="錯誤：請至少填寫一種題型的數量！")

    reqs = []
    if num_choice > 0: reqs.append(f"- 選擇題：共 {num_choice} 題 (每題皆須附上 A, B, C, D 四個選項)")
    if num_blank > 0: reqs.append(f"- 填充題：共 {num_blank} 題 (留空處以 ___ 表示)")
    if num_calc > 0: reqs.append(f"- 計算題/問答題：共 {num_calc} 題")
    reqs_str = "\n".join(reqs)
    json_format_prompt = (
        f"你是一位台灣的教師。請針對台灣【{grade}】的【{subject}】科目出題。\n"
        f"考卷中必須包含且只能包含以下題型及數量，其餘沒提到的題型請完全跳過：\n{reqs_str}\n"
        "請『嚴格且只回傳』一個符合以下結構的 JSON 陣列字串，不要包含任何 ```json 或額外聊天文字：\n"
        "[\n"
        "  {\n"
        "    \"id\": 1,\n"
        "    \"type\": \"choice\",\n"
        "    \"question\": \"題目(台灣繁體)\",\n"
        "    \"options\": [\"A) 選項1\", \"B) 選項2\", \"C) 選項3\", \"D) 選項4\"],\n"
        "    \"answer\": \"A\",\n"
        "    \"analysis\": \"極簡短解析一文即可\"\n"
        "  }\n"
        "]"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "你是一個只會回傳乾淨 JSON 陣列的台灣出題系統。絕對不要說任何非 JSON 的廢話。\n"
                        "出題規則：1. 完全使用繁體中文。 2. 考卷結構大標題分明。 "
                        "3. 為了節省空間確保大量出題不中斷，『analysis』解析欄位請嚴格控制在 15 個字以內！"
                    )
                },
                {"role": "user", "content": json_format_prompt}
            ],
            temperature=0.3,
            max_tokens=4096 
        )
        raw_json = completion.choices.message.content.strip()
        cached_questions = json.loads(raw_json)
        return render_template_string(HTML_TEMPLATE, questions=cached_questions, score=None, error=None)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, questions=None, score=None, error=f"AI 出題失敗。原因：{str(e)}")

@app.route('/submit', methods=['POST'])
def submit_quiz():
    global cached_questions
    if not cached_questions:
        return render_template_string(HTML_TEMPLATE, questions=None, score=None, error="測驗已過期，請重新設定出題。")

    results = []
    correct_count = 0
    gradable_count = 0

    for q in cached_questions:
        user_ans = request.form.get(f"q_{q['id']}", "").strip()
        correct_ans = str(q["answer"]).strip()
        is_correct = False
        
        if q["type"] != "calc":
            gradable_count += 1
            if q["type"] == "choice":
                is_correct = user_ans.upper() == correct_ans.upper() or user_ans.upper().startswith(correct_ans.upper())
            else:
                is_correct = user_ans == correct_ans
            if is_correct:
                correct_count += 1
        
        results.append({
            "type": q["type"],
            "question": q["question"],
            "user_ans": user_ans,
            "correct_ans": correct_ans,
            "is_correct": is_correct,
            "analysis": q["analysis"]
        })

    score = int((correct_count / gradable_count) * 100) if gradable_count > 0 else 100
    return render_template_string(HTML_TEMPLATE, questions=None, score=score, results=results, error=None)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
