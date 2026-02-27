#!/usr/bin/env python3
"""
家庭助手 - 完整版 v0.2
功能：语音对话 + 提醒 + 讲故事 + 音乐 + 百科问答
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# 配置
SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

# ========== 核心功能 ==========

def chat(text):
    """AI对话 - 用Ollama"""
    try:
        result = subprocess.run(
            ["ollama", "run", "qwen:0.5b", text],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip() if result.stdout else "抱歉，我没听清楚"
    except Exception as e:
        return f"对话出错: {str(e)[:50]}"

def tell_story(topic=None):
    """讲故事"""
    if not topic:
        topics = ["小红帽", "三只小猪", "丑小鸭", "皇帝的新装"]
        topic = topics[datetime.now().second % len(topics)]
    
    prompt = f"""请用适合5岁小朋友的方式，简单讲一下《{topic}》的故事。
要求：
- 简短（100字以内）
- 温馨
- 不要太复杂"""
    
    return chat(prompt)

def answer_question(question):
    """百科问答"""
    prompt = f"""请用简单易懂的方式回答这个问题（50字以内）：
{question}"""
    return chat(prompt)

def play_music(song_name=None):
    """播放音乐（模拟）"""
    if not song_name:
        return "你想听什么歌呢？"
    return f"正在播放: {song_name}..."

def set_reminder(time, content):
    """设置提醒"""
    reminder = {
        "time": time,
        "content": content,
        "created_at": datetime.now().isoformat()
    }
    
    path = MEMORY_DIR / "reminders.json"
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = {"reminders": []}
    
    data["reminders"].append(reminder)
    
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return f"好的，已设置提醒：{time} {content}"

# ========== 命令解析 ==========

def parse_command(text):
    """解析用户命令"""
    text = text.lower()
    
    # 讲故事
    if any(k in text for k in ["讲故事", "故事", "讲个故事", "给我讲故事"]):
        topic = None
        for t in ["小红帽", "三只小猪", "丑小鸭", "皇帝的新装", "白雪公主", "灰姑娘"]:
            if t in text:
                topic = t
                break
        return "story", tell_story(topic)
    
    # 播放音乐
    if any(k in text for k in ["放歌", "听歌", "播放", "音乐", "歌"]):
        song = None
        songs = ["童年", "简单爱", "夜空中最亮的星", "平凡之路"]
        for s in songs:
            if s in text:
                song = s
                break
        return "music", play_music(song)
    
    # 提醒
    if any(k in text for k in ["提醒", "叫我", "定个闹钟"]):
        # 简单解析时间
        import re
        time_match = re.search(r'(\d+)[点时]', text)
        time = time_match.group(1) + ":00" if time_match else "未知时间"
        content = text
        return "reminder", set_reminder(time, content)
    
    # 百科问答
    if any(k in text for k in ["为什么", "什么是", "怎么做", "如何", "为什么"]):
        return "qa", answer_question(text)
    
    # 默认对话
    return "chat", chat(text)

# ========== 网页服务 ==========

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 家庭助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 30px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .avatar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        h1 { text-align: center; color: #333; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 20px; }
        
        .quick-btns { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
        .quick-btn {
            flex: 1;
            min-width: 100px;
            padding: 15px;
            border: none;
            border-radius: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-size: 14px;
        }
        .quick-btn:hover { opacity: 0.9; transform: scale(0.98); }
        
        .chat-box {
            background: #f8f9fa;
            border-radius: 20px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .message { margin-bottom: 12px; padding: 12px; border-radius: 12px; max-width: 85%; }
        .message.user { background: #667eea; color: white; margin-left: auto; }
        .message.assistant { background: #f0f0f0; color: #333; }
        .message .time { font-size: 10px; opacity: 0.7; margin-top: 5px; }
        
        .input-area { display: flex; gap: 10px; }
        .input-area input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
        }
        .input-area input:focus { border-color: #667eea; }
        .input-area button {
            padding: 15px 25px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            color: white;
            cursor: pointer;
        }
        
        .mic-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #ff4757;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            margin-bottom: 15px;
        }
        .mic-btn:active { transform: scale(0.95); }
    </style>
</head>
<body>
    <div class="container">
        <div class="avatar">🏠</div>
        <h1>家庭助手</h1>
        <p class="subtitle">说话就能用</p>
        
        <div class="quick-btns">
            <button class="quick-btn" onclick="quickCmd('讲故事')">📖 讲故事</button>
            <button class="quick-btn" onclick="quickCmd('放歌')">🎵 放首歌</button>
            <button class="quick-btn" onclick="quickCmd('提醒')">⏰ 设提醒</button>
            <button class="quick-btn" onclick="quickCmd('百科')">❓ 问问题</button>
        </div>
        
        <div class="chat-box" id="chatBox">
            <div class="message assistant">
                你好！我是家庭助手～可以直接说话或打字跟我聊天！
                <div class="time">现在</div>
            </div>
        </div>
        
        <button class="mic-btn" onclick="startVoice()">🎤</button>
        
        <div class="input-area">
            <input type="text" id="chatInput" placeholder="说话或打字..." onkeypress="if(event.key==='Enter')sendMsg()">
            <button onclick="sendMsg()">发送</button>
        </div>
    </div>
    
    <script>
        function quickCmd(cmd) {
            document.getElementById('chatInput').value = cmd;
            sendMsg();
        }
        
        function sendMsg() {
            const input = document.getElementById('chatInput');
            const text = input.value.trim();
            if (!text) return;
            
            addMsg(text, 'user');
            input.value = '';
            
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(r => r.json())
            .then(data => {
                addMsg(data.reply, 'assistant');
            });
        }
        
        function addMsg(text, type) {
            const box = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = `message ${type}`;
            const time = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
            div.innerHTML = `${text}<div class="time">${time}</div>`;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }
        
        function startVoice() {
            if (!('webkitSpeechRecognition' in window)) {
                alert('浏览器不支持语音，请打字');
                return;
            }
            const r = new webkitSpeechRecognition();
            r.lang = 'zh-CN';
            r.onresult = e => {
                document.getElementById('chatInput').value = e.results[0][0].transcript;
                sendMsg();
            };
            r.start();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    text = data.get('text', '')
    
    cmd_type, reply = parse_command(text)
    
    return jsonify({
        "type": cmd_type,
        "reply": reply
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🏠 家庭助手 v0.2")
    print("访问地址: http://localhost:8080")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
