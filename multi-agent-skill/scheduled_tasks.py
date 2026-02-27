#!/usr/bin/env python3
"""
定时任务汇总脚本
- 每天8:30发送日程
- 每30分钟检查任务进度并汇报
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent
TASKS_FILE = SKILL_DIR / "tasks.json"
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def send_qq(message):
    """发送QQ消息"""
    # 转义换行
    msg_escaped = message.replace("\n", "\\n")
    cmd = f"{QQ_SEND} {TARGET_OPENID} \"{msg_escaped}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def daily_schedule():
    """每日日程汇报"""
    from reminder import daily_schedule_message
    msg = daily_schedule_message()
    if msg and "暂无日程" not in msg:
        send_qq(msg)

def task_progress():
    """任务进度汇报"""
    tasks = load_tasks()
    active = {k: v for k, v in tasks.items() if v.get("status") == "进行中"}
    
    if active:
        lines = ["📋 任务进度汇报："]
        for tid, t in active.items():
            lines.append(f"• {t.get('content', '')[:30]}... [{t.get('progress')}]")
        
        msg = "主人，小风现在给您汇报任务进度了～\n" + "\n".join(lines) + "\n～喵喵喵～\n进度汇报完毕！"
        send_qq(msg)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["daily", "progress"])
    args = parser.parse_args()
    
    if args.action == "daily":
        daily_schedule()
    elif args.action == "progress":
        task_progress()
