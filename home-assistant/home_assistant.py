#!/usr/bin/env python3
"""
家庭助手 - 完整版 v0.4
支持Skill模块化 + QQ/微信机器人驱动
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

# 导入模块
import sys
sys.path.insert(0, str(SKILL_DIR))

# ========== 核心功能 ==========

def chat(text):
    """AI对话"""
    from model_manager import chat as model_chat
    result = model_chat(text)
    return result.get("reply", "抱歉，我没有听清楚")

def search(query):
    """联网搜索"""
    try:
        # 尝试使用 DuckDuckGo HTML
        url = f"https://html.duckduckgo.com/html/?q={query}"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True, text=True
        )
        if result.stdout:
            # 简单解析
            lines = result.stdout.split('\n')
            results = []
            for line in lines:
                if 'a href="https://' in line and 'result__' in line:
                    # 提取标题和链接
                    import re
                    match = re.search(r'>([^<]+)</a>', line)
                    if match and len(results) < 3:
                        title = match.group(1)
                        url_match = re.search(r'href="([^"]+)"', line)
                        url = url_match.group(1) if url_match else ""
                        results.append({"title": title, "url": url})
            if results:
                return results
    except:
        pass
    
    # 备用：使用百度
    try:
        url = f"https://www.baidu.com/s?wd={query}&rn=3"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True, text=True
        )
        if result.stdout:
            import re
            titles = re.findall(r'aria-label="([^"]+)"', result.stdout)[:3]
            return [{"title": t, "url": f"https://www.baidu.com/s?wd={query}"} for t in titles]
    except:
        pass
    
    return [{"title": "搜索失败", "url": "", "snippet": "请稍后重试"}]

def tell_story(topic=None):
    """讲故事"""
    if not topic:
        topics = ["小红帽", "三只小猪", "丑小鸭", "皇帝的新装", "白雪公主", "狼来了"]
        topic = topics[datetime.now().second % len(topics)]
    
    prompt = f"""请用适合5岁小朋友的方式，简单讲一下《{topic}》的故事。
要求：简短（80字以内）"""
    
    return chat(prompt)

def play_music(song_name=None):
    """播放音乐"""
    if not song_name:
        return "你想听什么歌呢？"
    return f"🎵 正在播放: {song_name}..."

def get_weather(city="上海"):
    """查天气"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", f"wttr.in/{city}?format=%c%t"],
            capture_output=True, text=True
        )
        if result.stdout:
            return f"🌤️ {city}: {result.stdout.strip()}"
    except:
        pass
    return f"🌤️ {city}今天天气不错！"

def tell_joke():
    """讲笑话"""
    jokes = [
        "为什么数学书总是很伤心？因为它们有太多的难题！",
        "小明的妈妈为什么买洗衣机？因为爸爸太会'甩'锅了！",
        "为什么电脑很勤奋？因为它每天都要'工作'！",
    ]
    return jokes[datetime.now().second % len(jokes)]

def set_reminder(time, content):
    """设置提醒"""
    reminder = {"time": time, "content": content, "created_at": datetime.now().isoformat()}
    
    path = MEMORY_DIR / "reminders.json"
    if path.exists():
        data = json.load(open(path))
    else:
        data = {"reminders": []}
    
    data["reminders"].append(reminder)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return f"⏰ 已设置提醒：{time} {content}"

# ========== 命令解析 ==========

def parse_command(text):
    """解析用户命令"""
    text_lower = text.lower()
    
    # 搜索
    if any(k in text for k in ["搜索", "查一下", "search", "查"]):
        import re
        query = text
        for k in ["搜索", "查一下", "search", "查"]:
            query = query.replace(k, "")
        query = query.strip()
        if query:
            results = search(query)
            reply = "🔍 搜索结果：\n"
            for r in results[:3]:
                reply += f"• {r.get('title', '无标题')}\n"
            return "search", reply
        return "search", "请提供搜索关键词"
    
    # 讲故事
    if any(k in text for k in ["讲故事", "故事", "讲个故事"]):
        topic = None
        for t in ["小红帽", "三只小猪", "丑小鸭", "皇帝的新装", "白雪公主", "灰姑娘"]:
            if t in text:
                topic = t
                break
        return "story", tell_story(topic)
    
    # 音乐
    if any(k in text for k in ["放歌", "听歌", "播放", "音乐"]):
        song = None
        songs = ["童年", "简单爱", "夜空中最亮的星", "平凡之路"]
        for s in songs:
            if s in text:
                song = s
                break
        return "music", play_music(song)
    
    # 天气
    if any(k in text for k in ["天气", "气温", "温度"]):
        import re
        city_match = re.search(r'(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆)', text)
        city = city_match.group(1) if city_match else "上海"
        return "weather", get_weather(city)
    
    # 提醒
    if any(k in text for k in ["提醒", "叫我", "定个闹钟"]):
        import re
        time_match = re.search(r'(\d+)[点时]', text)
        time = time_match.group(1) + ":00" if time_match else "未知时间"
        return "reminder", set_reminder(time, text)
    
    # 笑话
    if any(k in text for k in ["笑话", "搞笑", "逗我笑"]):
        return "joke", tell_joke()
    
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
    
    from model_manager import get_status
    status = get_status()
    
    return jsonify({
        "type": cmd_type,
        "reply": reply,
        "model": status.get("current", "ollama")
    })

@app.route('/api/feedback', methods=['POST'])
def feedback_api():
    """接收反馈"""
    data = request.json
    text = data.get('text', '')
    
    # 保存反馈
    feedback_file = MEMORY_DIR / "feedbacks.json"
    feedbacks = {"feedbacks": []}
    if feedback_file.exists():
        feedbacks = json.load(open(feedback_file))
    
    feedbacks["feedbacks"].append({
        "text": text,
        "time": datetime.now().isoformat()
    })
    
    with open(feedback_file, "w") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})

@app.route('/api/status')
def status_api():
    from model_manager import get_status
    return jsonify(get_status())

# ========== QQ/微信消息处理 ==========

@app.route('/api/bot', methods=['POST'])
def bot_api():
    """接收QQ/微信消息并处理"""
    data = request.json
    message = data.get('message', '')
    sender = data.get('sender', 'unknown')
    
    if message:
        cmd_type, reply = parse_command(message)
        return jsonify({
            "success": True,
            "reply": reply,
            "sender": sender
        })
    
    return jsonify({"success": False})

if __name__ == '__main__':
    print("=" * 50)
    print("🏠 家庭助手 v0.4")
    print("访问地址: http://localhost:8080")
    print("QQ/微信消息接口: POST /api/bot")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
