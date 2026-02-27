#!/usr/bin/env python3
"""
多智能体调度 - OpenClaw 集成
作为skill被调用，处理助手调度和记忆管理
"""

import json
import re
import sys
import os
from pathlib import Path

# 配置路径
SKILL_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / "config.json"
MEMORY_DIR = SKILL_DIR / "memory"
SHARED_DIR = SKILL_DIR / "shared"

# 确保目录存在
MEMORY_DIR.mkdir(exist_ok=True)
SHARED_DIR.mkdir(exist_ok=True)

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "max_agents": 100,
        "agents": {}
    }

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_memory_path(agent_name: str) -> Path:
    safe_name = agent_name.replace("/", "_").replace("\\", "_")
    return MEMORY_DIR / f"{safe_name}.json"

def load_memory(agent_name: str) -> dict:
    path = get_memory_path(agent_name)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "agent_name": agent_name,
        "history": [],
        "knowledge": []
    }

def save_memory(agent_name: str, memory: dict):
    from datetime import datetime
    path = get_memory_path(agent_name)
    memory["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def detect_agent(message: str, config: dict) -> tuple:
    """检测消息中的助手名字"""
    agents = config.get("agents", {})
    
    # 按名字长度排序，优先匹配长名字
    sorted_agents = sorted(agents.keys(), key=len, reverse=True)
    
    for name in sorted_agents:
        # 各种触发模式
        patterns = [
            f"^{name}[:：]?",           # 小A: 帮我...
            f"^{name}\\s",              # 小A 帮我...
            f"^{name}[帮请让叫]",        # 小A帮...
            f"[帮请让叫]{name}",        # 帮小A...
            f"[，。、]{name}[:：]?",     # 小A，帮我...
            f"[，。、]{name}\\s",        # 小A 帮我...
        ]
        
        for pattern in patterns:
            if re.search(pattern, message):
                # 清理消息
                clean = re.sub(f"^{name}[:：]?\\s*", "", message)
                clean = re.sub(f"^{name}\\s*", "", message)
                clean = re.sub(f"^[帮请让叫]{name}\\s*", "", clean)
                clean = re.sub(f"[，。、]{name}[:：]?\\s*", "", clean)
                clean = re.sub(f"[，。、]{name}\\s*", "", clean)
                
                return name, clean.strip()
    
    return None, message

def build_system_prompt(agent_name: str, config: dict) -> str:
    """构建助手人格"""
    agents = config.get("agents", {})
    agent = agents.get(agent_name, {})
    
    role = agent.get("role", "助手")
    desc = agent.get("description", "无描述")
    
    # 加载历史
    memory = load_memory(agent_name)
    history = memory.get("history", [])[-10:]
    
    history_lines = []
    for h in history:
        role_label = "你" if h.get("role") == "assistant" else "用户"
        history_lines.append(f"{role_label}: {h.get('content', '')}")
    history_text = "\n".join(history_lines) if history_lines else "（暂无历史）"
    
    # 加载共享知识
    shared_path = SHARED_DIR / "knowledge.json"
    shared_text = ""
    if shared_path.exists():
        with open(shared_path, "r", encoding="utf-8") as f:
            shared = json.load(f)
        items = shared.get("items", [])[-10:]
        if items:
            shared_text = "\n".join([f"- {i.get('content')}" for i in items])
            shared_text = "\n\n## 共享知识库\n" + shared_text
    
    prompt = f"""你是{agent_name}，{role}。
{desc}

## 对话历史
{history_text}
{shared_text}

记住你是{agent_name}，用这个身份回复用户。现在用户对你说："""
    
    return prompt

def handle_command(message: str, config: dict) -> str:
    """处理管理命令"""
    msg = message.strip()
    
    # 列出助手
    if msg in ["列出助手", "助手列表", "有哪些助手", "list"]:
        agents = config.get("agents", {})
        if not agents:
            return "📋 暂无助手"
        
        lines = ["📋 已注册的助手："]
        for name, info in agents.items():
            mem = load_memory(name)
            hist_count = len(mem.get("history", []))
            lines.append(f"• {name}: {info.get('role')} (历史{hist_count}条)")
        return "\n".join(lines)
    
    # 添加助手
    if msg.startswith("添加 ") or msg.startswith("新增 ") or msg.startswith("添加助手 "):
        parts = msg.split(maxsplit=3)
        if len(parts) >= 3:
            name = parts[1].strip()
            role = parts[2].strip()
            desc = parts[3].strip() if len(parts) > 3 else ""
            
            if name in config["agents"]:
                return f"❌ {name} 已存在"
            if len(config["agents"]) >= config["max_agents"]:
                return f"❌ 已达上限({config['max_agents']}个)"
            
            config["agents"][name] = {
                "role": role,
                "description": desc,
                "model": "minimax-portal/MiniMax-M2.1"
            }
            save_config(config)
            
            # 初始化记忆
            save_memory(name, {
                "agent_name": name,
                "history": [],
                "knowledge": []
            })
            
            return f"✅ 已添加 {name}（{role}）"
        return "❌ 格式：添加 名字 角色 描述"
    
    # 删除助手
    if msg.startswith("删除 ") or msg.startswith("删除助手 "):
        parts = msg.split(maxsplit=2)
        if len(parts) >= 2:
            name = parts[1].strip()
            if name in config["agents"]:
                del config["agents"][name]
                save_config(config)
                return f"✅ 已删除 {name}（记忆保留）"
            return f"❌ {name} 不存在"
        return "❌ 格式：删除 名字"
    
    # 记忆状态
    if msg.startswith("记忆 "):
        parts = msg.split(maxsplit=1)
        if len(parts) >= 2:
            name = parts[1].strip()
            mem = load_memory(name)
            hist = len(mem.get("history", []))
            know = len(mem.get("knowledge", []))
            return f"📊 {name} - 历史{hist}条，知识{know}条"
        return "❌ 格式：记忆 名字"
    
    # 共享知识
    if msg.startswith("共享 "):
        parts = msg.split(maxsplit=1)
        if len(parts) >= 2:
            knowledge = parts[1].strip()
            shared_path = SHARED_DIR / "knowledge.json"
            
            if shared_path.exists():
                with open(shared_path, "r", encoding="utf-8") as f:
                    shared = json.load(f)
            else:
                shared = {"items": []}
            
            shared["items"].append({
                "content": knowledge,
                "added_at": None
            })
            
            with open(shared_path, "w", encoding="utf-8") as f:
                json.dump(shared, f, ensure_ascii=False, indent=2)
            
            return "✅ 已添加到共享知识库"
        return "❌ 格式：共享 知识内容"
    
    # 帮助
    if msg in ["help", "帮助", "命令"]:
        return """📖 命令列表：
- 小A/小B/小C... 呼唤助手
- 列出助手 查看所有助手
- 添加 名字 角色 描述 添加新助手
- 删除 名字 删除助手
- 记忆 名字 查看助手记忆状态
- 共享 知识内容 添加到共享知识库"""
    
    return None

def save_history(agent_name: str, role: str, content: str):
    """保存对话历史"""
    from datetime import datetime
    memory = load_memory(agent_name)
    memory.setdefault("history", []).append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # 限制长度
    if len(memory["history"]) > 100:
        memory["history"] = memory["history"][-100:]
    save_memory(agent_name, memory)

def main():
    """CLI测试用"""
    config = load_config()
    
    # 初始化默认助手
    default_agents = {
        "小A": {"role": "视觉设计师", "description": "负责主图和宣传视频制作"},
        "小B": {"role": "写作助手", "description": "负责各类文案写作"},
        "小C": {"role": "编程助手", "description": "负责代码编写"},
        "小D": {"role": "产品经理", "description": "负责产品规划"}
    }
    
    for name, info in default_agents.items():
        if name not in config["agents"]:
            config["agents"][name] = info
            save_memory(name, {"agent_name": name, "history": [], "knowledge": []})
    
    save_config(config)
    
    # 测试
    tests = [
        "小A帮我做个主图",
        "列出助手",
        "添加 小E 测试员 测试用",
        "记忆 小A"
    ]
    
    for t in tests:
        agent, msg = detect_agent(t, config)
        print(f"输入: {t}")
        print(f"  -> 助手: {agent}, 内容: {msg}")
        
        if not agent:
            result = handle_command(t, config)
            if result:
                print(f"  -> 命令: {result}")
        print()

if __name__ == "__main__":
    main()
