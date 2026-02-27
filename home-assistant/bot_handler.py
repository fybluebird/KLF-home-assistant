#!/usr/bin/env python3
"""
家庭助手 - QQ/微信消息接收器
让助手像OpenClaw一样可以通过QQ/微信来驱动
"""

import subprocess
import json
import threading
import time
from pathlib import Path

# 配置
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

# 消息回调
MESSAGE_CALLBACK = None

def set_callback(callback):
    """设置消息处理回调"""
    global MESSAGE_CALLBACK
    MESSAGE_CALLBACK = callback

def send_message(to_openid, message):
    """发送QQ消息"""
    msg_escaped = message.replace("\n", "\\n")
    subprocess.run(f"{QQ_SEND} {to_openid} \"{msg_escaped}\"", shell=True, capture_output=True)

def send_to_master(message):
    """发送消息给主人"""
    send_message(TARGET_OPENID, message)

def handle_qq_message(message):
    """处理收到的QQ消息"""
    print(f"收到QQ消息: {message}")
    
    if MESSAGE_CALLBACK:
        # 调用回调处理消息
        reply = MESSAGE_CALLBACK(message)
        if reply:
            send_to_master(reply)

class QQBot:
    """QQ机器人（轮询方式）"""
    
    def __init__(self):
        self.running = False
        self.last_message_id = None
    
    def check_messages(self):
        """检查新消息（简化版，实际需要webhook或长轮询）"""
        # 这里简化处理：不做主动拉取
        # 实际使用时，QQ消息通过OpenClaw的QQ渠道接收
        pass
    
    def start(self):
        """启动机器人"""
        self.running = True
        print("QQ机器人已启动（被动接收模式）")
    
    def stop(self):
        """停止机器人"""
        self.running = False

# 全局机器人实例
bot = QQBot()

def process_incoming_message(text, sender=None):
    """处理从QQ/微信接收的消息"""
    print(f"收到消息 from {sender}: {text}")
    
    # 导入skill系统
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from skills import execute_skill, get_skill
    from model_manager import chat
    
    text_lower = text.lower()
    
    # 解析命令
    if "搜索" in text or "查一下" in text or "search" in text_lower:
        # 提取搜索关键词
        query = text.replace("搜索", "").replace("查一下", "").replace("search", "").strip()
        result = execute_skill("search", {"query": query})
        if result.get("success"):
            reply = "搜索结果：\n"
            for r in result.get("results", [])[:3]:
                reply += f"• {r.get('title', '')}\n"
                reply += f"  {r.get('snippet', '')}...\n"
            return reply
    
    elif "天气" in text:
        import re
        city_match = re.search(r'(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆)', text)
        city = city_match.group(1) if city_match else "上海"
        result = execute_skill("weather", {"city": city})
        return result.get("weather", "")
    
    elif "讲故事" in text or "故事" in text:
        topic = None
        for t in ["小红帽", "三只小猪", "丑小鸭", "白雪公主", "灰姑娘"]:
            if t in text:
                topic = t
                break
        result = execute_skill("story", {"topic": topic})
        return result.get("story", "")
    
    elif "笑话" in text or "搞笑" in text:
        result = execute_skill("joke")
        return result.get("joke", "")
    
    elif "提醒" in text or "叫我" in text:
        import re
        time_match = re.search(r'(\d+)[点时]', text)
        time_val = time_match.group(1) + ":00" if time_match else "未知时间"
        result = execute_skill("reminder", {"time": time_val, "content": text})
        return result.get("message", "")
    
    elif "放歌" in text or "听歌" in text:
        result = execute_skill("music", {"song": text.replace("放歌", "").replace("听歌", "").strip()})
        return result.get("message", "")
    
    else:
        # 默认对话
        return chat(text)

if __name__ == "__main__":
    # 测试
    print("QQ消息处理测试:")
    print(process_incoming_message("今天天气怎么样"))
    print(process_incoming_message("给我讲个故事"))
    print(process_incoming_message("搜索python"))
