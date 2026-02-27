#!/usr/bin/env python3
"""
家庭管家系统 - Web仪表盘后端 V2
实时更新、任务分配、历史记录
"""

from flask import Flask, jsonify, render_template, request
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
import psutil

SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config.json"
MEMORY_DIR = SKILL_DIR / "memory"
TASKS_FILE = SKILL_DIR / "tasks.json"

app = Flask(__name__, template_folder=str(SKILL_DIR / "templates"))

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"agents": {}}

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_memory(agent_id):
    path = MEMORY_DIR / f"{agent_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"history": [], "knowledge": []}

def get_system_info():
    """获取系统资源"""
    # CPU
    cpu = psutil.cpu_percent(interval=0.5)
    
    # 内存
    mem = psutil.virtual_memory()
    mem_used = f"{mem.percent}%"
    
    # 磁盘
    disk = psutil.disk_usage('/')
    disk_used = f"{disk.percent}%"
    
    # 运行时间
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = f"{int(uptime.total_seconds()/3600)}h"
    
    # Ollama状态
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        ollama = "运行中" if result.returncode == 0 else "未运行"
    except:
        ollama = "未安装"
    
    # Cron状态
    try:
        result = subprocess.run(["pgrep", "-f", "cron"], capture_output=True, text=True)
        cron = "运行中" if result.returncode == 0 else "已停止"
    except:
        cron = "未知"
    
    return {
        "cpu": int(cpu),
        "memory": mem_used,
        "disk": disk_used,
        "uptime": uptime_str,
        "ollama": ollama,
        "cron": cron
    }

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/data')
def api_data():
    """主数据接口"""
    config = load_config()
    tasks = load_tasks()
    now = datetime.now()
    
    # 智能体数据
    agents = []
    total_memories = 0
    for agent_id, info in config.get("agents", {}).items():
        mem = load_memory(agent_id)
        history_count = len(mem.get("history", []))
        total_memories += history_count
        
        agents.append({
            "id": agent_id,
            "mainName": info.get("names", [agent_id])[0],
            "nickName": info.get("names", [""])[1] if len(info.get("names", [])) > 1 else "",
            "role": info.get("role", ""),
            "description": info.get("description", ""),
            "historyCount": history_count
        })
    
    # 进行中的任务
    active_tasks = []
    history_tasks = []
    for task_id, task in tasks.items():
        task_data = {
            "id": task_id,
            "content": task.get("content", ""),
            "progress": task.get("progress", "0%"),
            "status": task.get("status", ""),
            "updatedAt": task.get("updated_at", "")[:16],
            "note": task.get("note", "")
        }
        
        # 检查是否卡住
        if task.get("status") == "进行中":
            updated = datetime.fromisoformat(task.get("updated_at", "2026-01-01"))
            minutes = (now - updated).total_seconds() / 60
            task_data["isStuck"] = minutes > 10
            active_tasks.append(task_data)
        else:
            history_tasks.append(task_data)
    
    # 今日日程
    today_schedules = 0
    for agent_id in config.get("agents", {}):
        mem = load_memory(agent_id)
        for item in mem.get("knowledge", []):
            if item.get("type") == "日程" and str(now.date()) in item.get("content", ""):
                today_schedules += 1
    
    return jsonify({
        "agents": agents,
        "tasks": active_tasks,
        "historyTasks": history_tasks,
        "activeTaskCount": len(active_tasks),
        "totalMemories": total_memories,
        "todaySchedules": today_schedules,
        "system": get_system_info()
    })

@app.route('/api/system')
def api_system():
    """系统资源接口"""
    return jsonify(get_system_info())

@app.route('/api/task', methods=['POST'])
def api_task():
    """分配任务"""
    data = request.json
    agent_id = data.get('agentId')
    task_content = data.get('task')
    
    if not agent_id or not task_content:
        return jsonify({"error": "缺少参数"}), 400
    
    # 创建任务
    tasks = load_tasks()
    task_id = f"{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tasks[task_id] = {
        "agent_id": agent_id,
        "content": task_content,
        "status": "进行中",
        "progress": "0%",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "note": "等待执行"
    }
    
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 发送确认消息
    send_qq_message(f"✅ 主人，小风现在开始任务了哟～喵喵喵！\n\n任务内容：{task_content}\n\n分配给: {agent_id}")
    
    return jsonify({"success": True, "taskId": task_id})

@app.route('/api/task/complete', methods=['POST'])
def api_task_complete():
    """完成任务并发送消息"""
    data = request.json
    task_id = data.get('taskId')
    result = data.get('result', '')
    
    tasks = load_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = "已完成"
        tasks[task_id]["progress"] = "100%"
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        task = tasks[task_id]
        agent = task.get("agent_id", "")
        content = task.get("content", "")
        
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        # 发送完成消息
        msg = f"✅ 主人，任务已完成啦～喵喵喵！\n\n任务：{content}\n"
        if result:
            msg += f"结果：{result}\n"
        msg += "\n～喵喵喵～ 任务汇报完毕！"
        send_qq_message(msg)
        
        return jsonify({"success": True})
    
    return jsonify({"error": "任务不存在"}), 404

@app.route('/api/task/cancel', methods=['POST'])
def api_task_cancel():
    """取消任务并发送消息"""
    data = request.json
    task_id = data.get('taskId')
    
    tasks = load_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = "已取消"
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        task = tasks[task_id]
        content = task.get("content", "")
        
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        # 发送取消消息
        send_qq_message(f"❌ 主人，任务已取消～\n\n任务：{content}")
        
        return jsonify({"success": True})
    
    return jsonify({"error": "任务不存在"}), 404

def send_qq_message(message):
    """发送QQ消息"""
    try:
        cmd = f"node {SKILL_DIR}/send_qq.js 352983D4C8F36D56E350266944DF8DE1 \"{message}\""
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    except:
        pass

@app.route('/api/agents')
def api_agents():
    """智能体列表"""
    config = load_config()
    agents = []
    for agent_id, info in config.get("agents", {}).items():
        agents.append({
            "id": agent_id,
            "names": info.get("names", []),
            "role": info.get("role", ""),
            "description": info.get("description", "")
        })
    return jsonify(agents)

if __name__ == '__main__':
    print("=" * 50)
    print("🏠 家庭管家系统 - 控制面板 V2")
    print("=" * 50)
    print("🌐 访问地址: http://localhost:5000")
    print("📱 页面实时更新，每3秒刷新")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
