#!/usr/bin/env python3
"""
任务分发器
收到任务后立即确认，后台执行，完成后汇报结果
"""

import sys
import subprocess
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

def send_qq(message):
    """发送QQ消息"""
    msg_escaped = message.replace("\n", "\\n")
    cmd = f"{QQ_SEND} {TARGET_OPENID} \"{msg_escaped}\""
    subprocess.run(cmd, shell=True, capture_output=True)

def load_tasks():
    """加载任务列表"""
    tasks_file = SKILL_DIR / "tasks.json"
    if tasks_file.exists():
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def update_task_status(task_id, status, progress, note=""):
    """更新任务状态"""
    tasks = load_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = status
        tasks[task_id]["progress"] = progress
        if note:
            tasks[task_id]["note"] = note
        from datetime import datetime
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

def run_task_background(task_id, task_content):
    """后台执行任务"""
    # 这里可以根据任务内容执行不同的操作
    print(f"后台执行任务: {task_content}")
    
    # 模拟任务执行
    import time
    time.sleep(5)  # 模拟耗时任务
    
    # 完成后发送消息
    send_qq(f"✅ 任务完成！\n\n任务：{task_content}\n\n已完成，请查收～")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 task_dispatcher.py <任务ID> <任务内容>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    task_content = sys.argv[2]
    
    # 立即发送确认消息
    confirm_msg = f"✅ 主人，小风现在开始执行任务了哟～喵喵喵！\n\n任务内容：{task_content}"
    send_qq(confirm_msg)
    
    print(f"已发送确认消息: {task_content}")
    
    # 更新任务状态
    update_task_status(task_id, "进行中", "0%")
    
    # 后台执行任务（在后台运行这个脚本即可）
    print(f"任务已创建: {task_id}")
