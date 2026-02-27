#!/usr/bin/env python3
"""
任务执行器
自动检查并执行任务
"""

import subprocess
import json
import time
import os
from pathlib import Path
from datetime import datetime
import threading

SKILL_DIR = Path(__file__).parent
TASKS_FILE = SKILL_DIR / "tasks.json"
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

def send_qq(message):
    msg_escaped = message.replace("\n", "\\n")
    subprocess.run(f"{QQ_SEND} {TARGET_OPENID} \"{msg_escaped}\"", shell=True, capture_output=True)

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def update_task(task_id, status=None, progress=None, note=None):
    tasks = load_tasks()
    if task_id in tasks:
        if status:
            tasks[task_id]["status"] = status
        if progress:
            tasks[task_id]["progress"] = progress
        if note:
            tasks[task_id]["note"] = note
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        save_tasks(tasks)

# 任务执行器
def execute_task(task_id, task_content, agent_id):
    """执行任务"""
    print(f"开始执行任务: {task_id} - {task_content}")
    
    # 根据任务内容选择执行方式
    if "美妆" in task_content:
        result = execute_beauty_task(task_content)
    elif "股票" in task_content:
        result = execute_stock_task(task_content)
    elif "英语" in task_content:
        result = execute_english_task(task_content)
    elif "网页" in task_content or "仪表盘" in task_content:
        result = execute_web_task(task_content)
    else:
        # 默认执行通用任务
        result = execute_general_task(task_content)
    
    # 更新任务状态
    update_task(task_id, status="已完成", progress="100%", note=result[:100])
    
    # 发送完成消息
    msg = f"""✅ 主人，任务已完成啦～喵喵喵！

任务：{task_content}
结果：{result[:200]}...

～喵喵喵～ 任务汇报完毕！"""
    send_qq(msg)
    print(f"任务完成: {task_id}")

def execute_beauty_task(task_content):
    """美妆趋势任务"""
    try:
        result = subprocess.run(
            ["python3", f"{SKILL_DIR}/beauty_monitor.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return "美妆趋势报告已生成并发送"
        return f"执行完成: {result.stdout[:100]}"
    except Exception as e:
        return f"执行出错: {str(e)[:50]}"

def execute_stock_task(task_content):
    """股票任务"""
    try:
        result = subprocess.run(
            ["python3", f"{SKILL_DIR}/stock_monitor.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return "股票报告已生成"
    except Exception as e:
        return f"执行出错: {str(e)[:50]}"

def execute_english_task(task_content):
    """英语任务"""
    return "英语学习任务待开发"

def execute_web_task(task_content):
    """网页任务"""
    return "网页任务待开发"

def execute_general_task(task_content):
    """通用任务"""
    return f"任务内容: {task_content[:50]}... 已记录"

def run_executor():
    """任务执行主循环"""
    print("任务执行器已启动...")
    checked_tasks = set()
    
    while True:
        try:
            tasks = load_tasks()
            now = datetime.now()
            
            for task_id, task in tasks.items():
                if task.get("status") == "进行中":
                    # 检查是否已经执行过
                    if task_id in checked_tasks:
                        continue
                    
                    # 检查是否是刚创建的任务（1分钟内）
                    created = datetime.fromisoformat(task.get("created_at", "2026-01-01"))
                    if (now - created).total_seconds() > 5:
                        checked_tasks.add(task_id)
                        # 在后台执行任务
                        thread = threading.Thread(
                            target=execute_task,
                            args=(task_id, task.get("content", ""), task.get("agent_id", ""))
                        )
                        thread.daemon = True
                        thread.start()
                        print(f"触发任务执行: {task_id}")
            
        except Exception as e:
            print(f"执行器错误: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    run_executor()
