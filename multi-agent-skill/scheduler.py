#!/usr/bin/env python3
"""
多智能体调度 - v2.0版
支持编号+多名字匹配
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

# ===== 配置 =====
SKILL_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / "config.json"
MEMORY_DIR = SKILL_DIR / "memory"
SHARED_DIR = SKILL_DIR / "shared"
TASKS_FILE = SKILL_DIR / "tasks.json"

MEMORY_DIR.mkdir(exist_ok=True)
SHARED_DIR.mkdir(exist_ok=True)

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "2.0", "max_agents": 100, "agents": {}}

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_memory_path(name):
    return MEMORY_DIR / f"{name.replace('/', '_')}.json"

def load_memory(name):
    path = get_memory_path(name)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"agent_name": name, "history": [], "knowledge": []}

def save_memory(name, mem):
    path = get_memory_path(name)
    mem["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# ===== 任务管理 =====
def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def create_task(agent_id, task_content):
    tasks = load_tasks()
    task_id = f"{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tasks[task_id] = {
        "agent_id": agent_id,
        "content": task_content,
        "status": "进行中",
        "progress": "0%",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    save_tasks(tasks)
    return task_id

def update_task(task_id, progress=None, status=None):
    tasks = load_tasks()
    if task_id in tasks:
        if progress:
            tasks[task_id]["progress"] = progress
        if status:
            tasks[task_id]["status"] = status
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        save_tasks(tasks)

def get_all_tasks():
    return load_tasks()

# ===== 核心功能 =====
def detect_agent(msg, config):
    """检测助手 - 支持编号和多名字匹配"""
    agents = config.get("agents", {})
    
    # 构建名字→ID的映射
    name_to_id = {}
    for agent_id, info in agents.items():
        for name in info.get("names", [agent_id]):
            name_to_id[name] = agent_id
    
    # 按名字长度排序，优先匹配长名字
    sorted_names = sorted(name_to_id.keys(), key=len, reverse=True)
    
    for name in sorted_names:
        patterns = [
            f"^{name}[:：]?\\s*",
            f"^{name}\\s+",
            f"^{name}[帮请让叫]",
            f"[帮请让叫]{name}",
            f"[，。、]{name}[:：]?\\s*",
            f"[，。、]{name}\\s+",
        ]
        for p in patterns:
            if re.search(p, msg):
                clean = re.sub(p, "", msg)
                agent_id = name_to_id[name]
                return agent_id, clean.strip(), name  # 返回ID、被呼唤的名字、实际任务
    
    return None, msg, None

def get_agent_info(agent_id, config):
    """获取助手信息"""
    agents = config.get("agents", {})
    return agents.get(agent_id, {})

def get_agent_display_name(agent_id, config):
    """获取助手显示名（主名）"""
    info = get_agent_info(agent_id, config)
    names = info.get("names", [agent_id])
    return names[0]  # 返回主名

def build_system_prompt(agent_id, config):
    """构建助手人格prompt"""
    info = get_agent_info(agent_id, config)
    
    role = info.get("role", "助手")
    desc = info.get("description", "无描述")
    names = info.get("names", [agent_id])
    main_name = names[0]
    
    mem = load_memory(agent_id)
    history = mem.get("history", [])[-10:]
    
    hist_lines = []
    for h in history:
        label = "你" if h.get("role") == "assistant" else "用户"
        hist_lines.append(f"{label}: {h.get('content', '')}")
    hist_text = "\n".join(hist_lines) or "（暂无历史）"
    
    # 共享知识
    shared_path = SHARED_DIR / "knowledge.json"
    shared_text = ""
    if shared_path.exists():
        with open(shared_path, "r", encoding="utf-8") as f:
            shared = json.load(f)
        items = shared.get("items", [])[-10:]
        if items:
            shared_text = "\n\n## 共享知识\n" + "\n".join([f"- {i.get('content')}" for i in items])
    
    return f"""你是{agent_id}智能体，主名「{main_name}」，{role}。
{desc}

## 可用名字：{"、".join(names)}

## 对话历史
{hist_text}
{shared_text}

你是{main_name}，用这个身份专业地回复用户。"""

def handle_command(msg, config):
    """管理命令"""
    msg = msg.strip()
    
    # 列出助手
    if msg in ["列出助手", "助手列表", "list", "有哪些助手", "状态", "智能体"]:
        agents = config.get("agents", {})
        if not agents:
            return "📋 暂无智能体"
        lines = ["📋 已注册的智能体："]
        for aid, info in agents.items():
            names = info.get("names", [aid])
            main_name = names[0]
            mem = load_memory(aid)
            cnt = len(mem.get("history", []))
            agt_tasks = {k: v for k, v in get_all_tasks().items() if v.get("agent_id") == aid and v.get("status") == "进行中"}
            status = f" (任务: {len(agt_tasks)}进行中)" if agt_tasks else ""
            lines.append(f"• {aid} | 主名「{main_name}」| {info.get('role')} (历史{cnt}条){status}")
        return "\n".join(lines)
    
    # 添加智能体
    if msg.startswith("添加 ") or msg.startswith("添加智能体 "):
        parts = msg.split(maxsplit=4)
        if len(parts) >= 3:
            agent_id = parts[1].strip()
            role = parts[2].strip()
            names_raw = parts[3].strip() if len(parts) > 3 else ""
            desc = parts[4].strip() if len(parts) > 4 else ""
            
            # 解析名字列表
            names = [agent_id]
            if names_raw:
                names = [agent_id] + names_raw.split("、")
            names = names[:3]  # 最多3个
            
            if agent_id in config["agents"]:
                return f"❌ {agent_id} 已存在"
            if len(config["agents"]) >= config["max_agents"]:
                return f"❌ 已达上限{config['max_agents']}"
            
            config["agents"][agent_id] = {
                "names": names,
                "role": role,
                "description": desc
            }
            save_config(config)
            save_memory(agent_id, {"agent_name": agent_id, "history": [], "knowledge": []})
            return f"✅ 已添加 {agent_id}「{names[0]}」({role})"
        return "❌ 格式：添加 编号 角色 名字列表 描述"
    
    # 删除智能体
    if msg.startswith("删除 ") or msg.startswith("删除智能体 "):
        parts = msg.split(maxsplit=2)
        if len(parts) >= 2:
            agent_id = parts[1].strip()
            if agent_id in config["agents"]:
                del config["agents"][agent_id]
                save_config(config)
                return f"✅ 已删除 {agent_id}（记忆保留）"
            return f"❌ {agent_id} 不存在"
        return "❌ 格式：删除 编号"
    
    # 记忆详情
    if msg.startswith("记忆 ") or msg.startswith("查看记忆 "):
        parts = msg.split(maxsplit=1)
        if len(parts) >= 2:
            query = parts[1].strip()
            # 支持编号或名字查询
            agent_id, _, _ = detect_agent(query, config)
            if not agent_id:
                # 直接当ID处理
                agent_id = query
            mem = load_memory(agent_id)
            hist = mem.get("history", [])
            return f"📊 {agent_id} 历史{len(hist)}条"
        return "❌ 格式：记忆 编号"
    
    # 任务列表
    if msg in ["任务", "任务列表", "所有任务"]:
        tasks = get_all_tasks()
        active = {k: v for k, v in tasks.items() if v.get("status") == "进行中"}
        if not active:
            return "📋 暂无进行中的任务"
        lines = ["📋 进行中的任务："]
        for tid, t in active.items():
            lines.append(f"  • {t.get('agent_id')}: {t.get('content', '')[:30]}... [{t.get('progress')}]")
        return "\n".join(lines)
    
    # 共享知识
    if msg.startswith("共享 "):
        parts = msg.split(maxsplit=1)
        if len(parts) >= 2:
            content = parts[1]
            shared_path = SHARED_DIR / "knowledge.json"
            if shared_path.exists():
                with open(shared_path, "r") as f:
                    shared = json.load(f)
            else:
                shared = {"items": []}
            shared["items"].append({"content": content, "added_at": datetime.now().isoformat()})
            with open(shared_path, "w") as f:
                json.dump(shared, f, ensure_ascii=False, indent=2)
            return "✅ 已添加到共享知识库"
        return "❌ 格式：共享 内容"
    
    # 帮助
    if msg in ["help", "帮助", "命令"]:
        return """📖 命令：
🎯 呼唤智能体：001、002... 或 主名/昵称
📋 管理：列出助手 / 添加 编号 角色 名字 / 删除 编号
📊 记忆：记忆 编号
📋 任务：任务 / 任务列表"""
    
    return None

def save_history(agent_id, role, content):
    mem = load_memory(agent_id)
    mem.setdefault("history", []).append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    if len(mem["history"]) > 100:
        mem["history"] = mem["history"][-100:]
    save_memory(agent_id, mem)

# ===== 进度汇报 =====
START_TEMPLATE = "主人，小风现在开始{agent}的任务了哟～喵喵喵！\n任务内容：{task}"
REPORT_TEMPLATE = "主人，小风现在给您汇报{agent}任务的进度了～\n当前进度：{progress}\n～喵喵喵～\n进度汇报完毕，继续执行任务！"

def get_task_report(agent_id=None):
    tasks = get_all_tasks()
    if agent_id:
        tasks = {k: v for k, v in tasks.items() if v.get("agent_id") == agent_id}
    
    active = {k: v for k, v in tasks.items() if v.get("status") == "进行中"}
    
    if not active:
        return "主人，小风现在没有进行中的任务哦～喵喵喵！"
    
    lines = ["📋 任务进度汇报："]
    for tid, t in active.items():
        lines.append(f"  • {t.get('agent_id')}: {t.get('content', '')[:25]}...")
        lines.append(f"    进度: {t.get('progress')} | 状态: {t.get('status')}")
    
    return "主人，小风现在给您汇报任务进度了～\n" + "\n".join(lines) + "\n～喵喵喵～\n进度汇报完毕，继续执行任务！"

# ===== 入口 =====
if __name__ == "__main__":
    config = load_config()
    
    # 测试
    print("=== v2.0 测试 ===")
    tests = [
        "001 帮我做个主图",
        "小B 写一篇文案", 
        "小文帮我写首诗",
        "列出助手",
        "任务"
    ]
    
    for t in tests:
        agent_id, msg, called_name = detect_agent(t, config)
        print(f"📩 {t}")
        if agent_id:
            info = get_agent_info(agent_id, config)
            main_name = info.get("names", [agent_id])[0]
            print(f"   -> 编号: {agent_id}, 主名: {main_name}, 任务: {msg}")
            task_id = create_task(agent_id, msg)
            print(f"   {START_TEMPLATE.format(agent=main_name, task=msg)}")
        else:
            result = handle_command(t, config)
            if result:
                print(f"   -> {result}")
        print()
