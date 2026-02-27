#!/usr/bin/env python3
"""
家庭助手 - 完整版 v0.3
功能：语音对话 + 提醒 + 讲故事 + 音乐 + 百科 + 反馈系统
支持本地+云端多模型
"""

import subprocess
import json
import os
import requests
from datetime import datetime
from pathlib import Path

# 配置
SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

# 导入模型管理器
import sys
sys.path.insert(0, str(SKILL_DIR))
from model_manager import chat as model_chat, get_status, load_config

# ========== 核心功能 ==========

def chat(text):
    """AI对话 - 优先云端，本地备用"""
    result = model_chat(text)
    return result.get("reply", "抱歉，我没有听清楚")

def tell_story(topic=None):
    """讲故事"""
    if not topic:
        topics = ["小红帽", "三只小猪", "丑小鸭", "皇帝的新装", "白雪公主", "狼来了"]
        topic = topics[datetime.now().second % len(topics)]
    
    prompt = f"""请用适合5岁小朋友的方式，简单讲一下《{topic}》的故事。
要求：
- 简短（80字以内）
- 温馨
- 不要太复杂"""
    
    return chat(prompt)

def play_music(song_name=None):
    """播放音乐（模拟）"""
    if not song_name:
        return "你想听什么歌呢？"
    return f"🎵 正在播放: {song_name}..."

def get_weather(city="上海"):
    """查天气"""
    try:
        # 用wttr.in免费天气
        result = subprocess.run(
            ["curl", "-s", f"wttr.in/{city}?format=%c%t+%h"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout:
            return f"🌤️ {city}天气: {result.stdout.strip()}"
    except:
        pass
    
    # 备用：简单回复
    return f"🌤️ {city}今天天气不错，适合出去玩！"

def tell_joke():
    """讲笑话"""
    jokes = [
        "为什么数学书总是很伤心？因为它们有太多的难题（难题）",
        "小明的妈妈为什么买洗衣机？因为爸爸太会'甩'锅了！",
        "为什么电脑很勤奋？因为它每天都要'工作'（作业）",
        "有一天，小鸡问妈妈：妈妈妈妈，我们为什么是鸡？妈妈说：因为我们是'鸡'极向上！"
    ]
    return jokes[datetime.now().second % len(jokes)]

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
    
    return f"⏰ 好的，已设置提醒：{time} {content}"

# ========== 命令解析 ==========

def parse_command(text):
    """解析用户命令"""
    text_lower = text.lower()
    
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
    
    # 天气
    if any(k in text for k in ["天气", "气温", "温度", "晴天", "下雨"]):
        import re
        city_match = re.search(r'(北京|上海|广州|深圳|杭州|南京|成都|武汉)', text)
        city = city_match.group(1) if city_match else "上海"
        return "weather", get_weather(city)
    
    # 提醒
    if any(k in text for k in ["提醒", "叫我", "定个闹钟", "设个提醒"]):
        import re
        time_match = re.search(r'(\d+)[点时]', text)
        time = time_match.group(1) + ":00" if time_match else "未知时间"
        content = text
        return "reminder", set_reminder(time, content)
    
    # 笑话
    if any(k in text for k in ["笑话", "搞笑", "讲个笑话", "逗我笑"]):
        return "joke", tell_joke()
    
    # 百科问答
    if any(k in text for k in ["为什么", "什么是", "怎么做", "如何", "为什么"]):
        return "qa", chat(text)
    
    # 默认对话
    return "chat", chat(text)

# ========== 网页服务 ==========

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
app.template_folder = str(SKILL_DIR / "templates")

@app.route('/')
def index():
    return render_template('index_v2.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    text = data.get('text', '')
    
    cmd_type, reply = parse_command(text)
    
    # 获取当前模型
    status = get_status()
    model_name = status.get("current", "ollama")
    
    return jsonify({
        "type": cmd_type,
        "reply": reply,
        "model": model_name
    })

@app.route('/api/feedback', methods=['POST'])
def feedback_api():
    """接收反馈并发送到QQ"""
    data = request.json
    text = data.get('text', '')
    
    # 保存反馈
    feedback_file = MEMORY_DIR / "feedbacks.json"
    if feedback_file.exists():
        with open(feedback_file, "r") as f:
            feedbacks = json.load(f)
    else:
        feedbacks = {"feedbacks": []}
    
    feedbacks["feedbacks"].append({
        "text": text,
        "time": datetime.now().isoformat()
    })
    
    with open(feedback_file, "w") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    
    # 发送到QQ
    try:
        QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
        TARGET = "352983D4C8F36D56E350266944DF8DE1"
        
        msg = f"""📢 收到新反馈啦！

{text}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        subprocess.run(f"{QQ_SEND} {TARGET} \"{msg}\"", shell=True, capture_output=True)
    except:
        pass
    
    return jsonify({"success": True})

@app.route('/api/status')
def status_api():
    """获取状态"""
    return jsonify(get_status())

if __name__ == '__main__':
    print("=" * 50)
    print("🏠 家庭助手 v0.3")
    print("访问地址: http://localhost:8080")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
