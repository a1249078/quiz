import os
import json
from flask import Flask, request, render_template_string
from groq import Groq

app = Flask(__name__)

# 初始化 Groq 客戶端（自動讀取 Render 設定的 GROQ_API_KEY）
client = Groq()

cached_questions = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI 台灣線上互動測驗系統</title>
    <style>
        body { font-family: "Microsoft JhengHei", Arial, sans-serif; max-width: 900px; margin: 30px auto; padding: 0 20px; line-height: 1.6; color: #333; background-color: #f8f9fa; }
        .setup-box { background: #ffffff; border: 1px solid #e0e0e0; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
        h2, h3, .q-title { color: #0056b3 !important; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #444; }
        input[type="text"], input[type="number"] { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        .btn-generate { background-color: #007bff; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; border-radius: 6px; font-weight: bold; width: 100%; margin-top: 10px; }
        .btn-generate:hover { background-color: #0056b3; }
        
        /* ⏱️ 浮動時間提醒框樣式 */
        .timer-float { position: fixed; top: 20px; right: 20px; background: rgba(0, 0, 0, 0.85); color: #fff; padding: 15px; border-radius: 10px; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 1000; line-height: 1.4; width: 160px; }
        .timer-val { font-size: 18px; font-weight: bold; color: #ffc107; font-family: monospace; }
        
        .exam-area { background: #ffffff; border: 1px solid #dee2e6; padding: 35px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .q-card { background: #ffffff; border: 1px solid #eaeaea; padding: 20px; margin-bottom: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .q-title { font-weight: bold; font-size: 18px; margin-bottom: 15px; }
        
        /* 雙欄並排布局 (一排 2 個選項) */
        .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
        .option-lbl { background: #fdfdfd; border: 1px solid #e2e8f0; padding: 10px 15px; cursor: pointer; border-radius: 6px; display: flex; align-items: center; gap: 8px; transition: all 0.2s; }
        .option-lbl:hover { background-color: #f1f5f9; border-color: #cbd5e1; }
        
        /* 計算題後方輸入框 */
        .calc-inline { display: flex; align-items: center; gap: 10px; width: 100%; margin-top: 8px; }
        .calc-input { flex: 1; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; }
        
        /* 動態提示按鈕 */
        .btn-hint { background: #17a2b8; color: white; border: none; padding: 5px 12px; font-size: 13px; border-radius: 4px; cursor: pointer; margin-top: 10px; font-weight: bold; }
        .hint-text { background: #e2f4f7; padding: 10px; border-radius: 6px; margin-top: 8px; color: #0f6674; font-size: 14px; display: none; border-left: 4px solid #17a2b8; }
        
        .score-board { text-align: center; background: #fff3cd; border: 2px dashed #ffc107; padding: 20px; border-radius: 8px; margin-bottom: 25px; }
        .score { font-size: 48px; color: #dc3545; font-weight: bold; }
        .report-card { border: 1px solid #dee2e6; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        .correct { border-left: 5px solid #28a745; background: #f4faf5; }
        .wrong { border-left: 5px solid #dc3545; background: #fff5f5; }
        
        .footer-btns { display: flex; gap: 15px; margin-top: 30px; }
        .btn-submit { flex: 2; background-color: #28a745; color: white; border: none; padding: 15px; font-size: 18px; cursor: pointer; border-radius: 6px; font-weight: bold; }
        .btn-clear { flex: 1; background-color: #6c757d; color: white; border: none; padding: 15px; font-size: 16px; cursor: pointer; border-radius: 6px; font-weight: bold; }
        .btn-submit:hover { background-color: #218838; }
        .btn-clear:hover { background-color: #5a6268; }
    </style>
</head>
<body>

    <!-- ⏱️ 浮動時間提醒框 -->
    <div class="timer-float" id="timerBox">
        <div>⏱️ 總用時: <span class="timer-val" id="totalTime">00:00</span></div>
        <div style="margin-top: 5px;">⏳ 剩餘時間: <span class="timer-val" id="limitTime">90:00</span></div>
    </div>

    <!-- 頂端分數顯示區 -->
    <div id="topScoreBoard" style="display:none;"></div>

    <div class="setup-box">
        <h3 style="margin-top:0;">📝 AI 台灣線上互動測驗系統</h3>
        <form method="POST" action="/generate">
            <div class="row">
                <div class="col form-group">
                    <label>學生年級</label>
                    <input type="text" name="grade" placeholder="例如：國中一年級" required>
                </div>
                <div class="col form-group">
                    <label>考試科目 / 範圍</label>
                    <input type="text" name="subject" placeholder="例如：數學（二元一次方程式）" required>
                </div>
            </div>
            <div class="row">
                <div class="col form-group"><label>是非題數</label><input type="number" name="num_tf" min="0" value="0"></div>
                <div class="col form-group"><label>選擇題數</label><input type="number" name="num_choice" min="0" value="0"></div>
                <div class="col form-group"><label>填空題數</label><input type="number" name="num_blank" min="0" value="0"></div>
                <div class="col form-group"><label>計算題數</label><input type="number" name="num_calc" min="0" value="0"></div>
            </div>
            <button type="submit" class="btn-generate">🚀 立即在下方生成並開始線上作答</button>
        </form>
    </div>

    {% if error %} <p style="color:red; font-weight:bold;">{{ error }}</p> {% endif %}

    {% if questions %}
    <div class="exam-area" id="examArea">
        <h3>✏️ 線上測驗開始（請直接在下方答題，進度將自動保存）</h3>
        <form id="quizForm" action="/submit" method="POST">
            {% for q in questions %}
            <div class="q-card">
                <!-- 題目文字用藍色 -->
                <div class="q-title">{{ loop.index }}. 〖{{ "是非題" if q.type == "tf" else "選擇題" if q.type == "choice" else "填空題" if q.type == "blank" else "計算題" }}〗{{ q.question }}</div>
                
                {% if q.type == "tf" %}
                    <div class="options-grid">
                        <label class="option-lbl"><input type="radio" name="q_{{ q.id }}" value="○" onchange="saveProgress('q_{{ q.id }}', '○')"> ○ 對</label>
                        <label class="option-lbl"><input type="radio" name="q_{{ q.id }}" value="╳" onchange="saveProgress('q_{{ q.id }}', '╳')"> ╳ 錯</label>
                    </div>
                {% elif q.type == "choice" %}
                    <!-- 選項一排 2 個 (雙欄並排) -->
                    <div class="options-grid">
                        {% for opt in q.options %}
                        <label class="option-lbl"><input type="radio" name="q_{{ q.id }}" value="{{ opt }}" onchange="saveProgress('q_{{ q.id }}', '{{ opt }}')"> {{ opt }}</label>
                        {% endfor %}
                    </div>
                {% elif q.type == "blank" %}
                    <input type="text" name="q_{{ q.id }}" class="txt-input" placeholder="請在此處輸入答案" oninput="saveProgress('q_{{ q.id }}', this.value)">
                {% else %}
                    <!-- 計算題：答案框直接在正後方 -->
                    <div class="calc-inline">
                        <span>✍️ 解答輸入位置：</span>
                        <input type="text" name="q_{{ q.id }}" class="calc-input" placeholder="請寫出最終答案或簡述算式" oninput="saveProgress('q_{{ q.id }}', this.value)">
                    </div>
                {% endif %}
                
                <!-- 💡 每道題目最後端的「解題提示」按鈕 -->
                <button type="button" class="btn-hint" onclick="toggleHint('hint_{{ q.id }}')">💡 顯示/隱藏解題提示</button>
                <div class="hint-text" id="hint_{{ q.id }}">{{ q.hint }}</div>
            </div>
            {% endfor %}
            
            <div class="footer-btns">
                <button type="button" class="btn-submit" onclick="submitAndScore()">💯 填寫完畢 計算得分</button>
                <button type="button" class="btn-clear" onclick="clearSavedProgress()">🧹 清除歷史作答進度</button>
            </div>
        </form>
    </div>
    {% endif %}

    {% if score is not none %}
    <script>
        // 後台交卷後，把結果動態灌回頂部
        document.addEventListener("DOMContentLoaded", function() {
            var sb = document.getElementById("topScoreBoard");
            sb.style.display = "block";
            sb.innerHTML = `<div class="score-board"><h2>📊 測驗批改報告</h2><div class="score">${ {{ score }} } / 100 分</div></div><h3>🔍 題目詳細解析：</h3>`;
            window.scrollTo({ top: 0, behavior: 'smooth' });
            localStorage.clear(); // 真正交卷成功後，清除快取
        });
    </script>
    <div class="exam-area" style="margin-top: 20px;">
        {% for r in results %}
        <div class="report-card {{ 'correct' if r.is_correct else 'wrong' if r.type == 'calc' else 'wrong' }}" style="border-left: 5px solid {% if r.type == 'calc' %}#6c757d{% elif r.is_correct %}#28a745{% else %}#dc3545{% endif %};">
            <strong>第 {{ loop.index }} 題：{{ r.question }}</strong><br>
            ✍️ 您的答案：<span style="font-weight:bold;">{{ r.user_ans }}</span><br>
            {% if r.type != 'calc' and not r.is_correct %} ✅ 正確答案：<span style="color: #28a745; font-weight: bold;">{{ r.correct_ans }}</span><br> {% endif %}
            <div style="background: #e9ecef; padding: 10px; font-size: 14px; margin-top:8px; border-radius:4px;">💡 <b>老師完整解析：</b>{{ r.analysis }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    <script>
        // 1. 動態切換顯示提示
        function toggleHint(id) {
            var el = document.getElementById(id);
            el.style.display = (el.style.display === 'block') ? 'none' : 'block';
        }

        // 2. localStorage 記憶防斷線技術
        function saveProgress(key, val) { localStorage.setItem(key, val); }
        function loadProgress() {
            if(!document.getElementById("quizForm")) return;
            var inputs = document.getElementById("quizForm").elements;
            for (var i = 0; i < inputs.length; i++) {
                var item = inputs[i];
                var saved = localStorage.getItem(item.name);
                if (saved) {
                    if (item.type === 'radio') {
                        if (item.value === saved) item.checked = true;
                    } else { item.value = saved; }
                }
            }
        }
        function clearSavedProgress() { localStorage.clear(); location.reload(); }

        // 3. 計算得分按鈕（觸發原表單送出）
        function submitAndScore() {
            if(document.getElementById("quizForm")) document.getElementById("quizForm").submit();
        }

        // ⏱️ 4. 浮動計時器雙系統運作邏輯
        var totalSec = 0;
        var limitSec = 90 * 60; // 90分鐘轉換為秒
        var alertTriggered = false;

        function updateTimers() {
            totalSec++;
            if (!alertTriggered) {
                limitSec--;
                if (limitSec <= 0) {
                    limitSec = 0;
                    alertTriggered = true;
                    alert("90分鐘以到你是大笨蛋"); // 超時彈窗，點擊取消後還能繼續
                }
            }
            // 轉換為 MM:SS 格式
            document.getElementById("totalTime").innerText = formatTime(totalSec);
            document.getElementById("limitTime").innerText = formatTime(limitSec);
        }
        function formatTime(s) {
            var m = Math.floor(s / 60); var sec = s % 60;
            return (m < 10 ? "0"+m : m) + ":" + (sec < 10 ? "0"+sec : sec);
        }

        if(document.getElementById("examArea")) {
            loadProgress();
            setInterval(updateTimers, 1000);
        }
    </script>
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
    
    # 嚴格讀取題型數量
    num_tf = int(request.form.get('num_tf', 0)) if request.form.get('num_tf') else 0
    num_choice = int(request.form.get('num_choice', 0)) if request.form.get('num_choice') else 0
    num_blank = int(request.form.get('num_blank', 0)) if request.form.get('num_blank') else 0
    num_calc = int(request.form.get('num_calc', 0)) if request.form.get('num_calc') else 0

    if num_tf == 0 and num_choice == 0 and num_blank == 0 and num_calc == 0:
        return render_template_string(HTML_TEMPLATE, questions=None, score=None, error="錯誤：請至少填寫一種題型的數量！")

    # 確保 AI 嚴格按照「是非題、選擇題、填空題、計算題」的順序產出 JSON 陣列
    json_format_prompt = (
        f"你是一位台灣教師。請針對台灣【{grade}】的【{subject}】科目出題。\n"
        f"考卷中必須『嚴格按照以下順序』依序產生對應題型，若數量為0請直接跳過：\n"
        f"1. 是非題：共 {num_tf} 題 (正確答案固定填入 '○' 或 '╳')\n"
        f"2. 選擇題：共 {num_choice} 題 (每題須附 A,B,C,D 四個選項，答案填 A/B/C/D)\n"
        f"3. 填空題：共 {num_blank} 題 (題目留空以 ___ 表示)\n"
        f"4. 計算題：共 {num_calc} 題 (題目最後不要留大面積空格)\n\n"
        "請『嚴格且只回傳』一個乾淨的 JSON 陣列字串，格式如下，『analysis』和『hint』請保持在 15 字以內防止斷線：\n"
        "[\n"
        "  {\n"
        "    \"id\": 1,\n"
        "    \"type\": \"tf\",\n"
        "    \"question\": \"是非題題目內容\",\n"
        "    \"options\": [],\n"
        "    \"answer\": \"○\",\n"
        "    \"hint\": \"這題的解題提示\",\n"
        "    \"analysis\": \"答案解析\"\n"
        "  }\n"
        "]"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "你是一個只會回傳乾淨 JSON 陣列的台灣出題系統。完全使用繁體中文。請嚴格遵守題目指定的題型先後順序產出資料。"},
                {"role": "user", "content": json_format_prompt}
            ],
            temperature=0.3, max_tokens=4096 
        )
        raw_json = completion.choices[0].message.content.strip()
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
            if q["type"] in ["choice", "tf"]:
                is_correct = user_ans.upper() == correct_ans.upper() or user_ans.upper().startswith(correct_ans.upper())
            else:
                is_correct = user_ans == correct_ans
            if is_correct: correct_count += 1
        
        results.append({
            "type": q["type"], "question": q["question"], "user_ans": user_ans,
            "correct_ans": correct_ans, "is_correct": is_correct, "analysis": q["analysis"]
        })

    score = int((correct_count / gradable_count) * 100) if gradable_count > 0 else 100
    return render_template_string(HTML_TEMPLATE, questions=None, score=score, results=results, error=None)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
