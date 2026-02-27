# 家庭管家系统 - 技术实现说明文档

> 版本：v2.0 | 更新日期：2026-02-27

---

## 一、系统实现概述

### 1.1 技术架构

本系统采用**总管家+多智能体协作模式**，基于Python实现，所有数据存储在本地JSON文件中。

```
┌─────────────────────────────────────────────────────┐
│                   用户 (QQ/飞书)                     │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              总助手 (我 - 小风)                       │
│  • 实时接收指令                                      │
│  • 秒回确认                                          │
│  • 任务分配                                          │
│  • 结果汇总                                          │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              智能体调度层 (scheduler.py)             │
│  • 检测助手名字                                       │
│  • 路由到对应智能体                                   │
│  • 任务状态管理                                       │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
    ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
    │ 001 │   │ 002 │   │ 003 │   │ 004 │
    │记忆 │   │开发 │   │编程 │   │产品 │
    │助手 │   │助手 │   │助手 │   │经理 │
    └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘
       │         │         │         │
       ▼         ▼         ▼         ▼
    ┌─────────────────────────────────────────┐
    │           本地存储层 (JSON)             │
    │  • config.json (智能体配置)            │
    │  • memory/*.json (记忆)                │
    │  • tasks.json (任务状态)               │
    │  • settings.json (用户设置)            │
    └─────────────────────────────────────────┘
```

### 1.2 脚本文件清单

| 文件名 | 语言 | 核心功能 |
|--------|------|----------|
| `scheduler.py` | Python 3 | 智能体调度、任务分配、名字检测 |
| `reminder.py` | Python 3 | 日程提醒计算、定时触发 |
| `report.py` | Python 3 | 任务进度汇报生成 |
| `agent.py` | Python 3 | 旧版调度器（已废弃） |
| `config.json` | JSON | 智能体配置与定义 |
| `memory/*.json` | JSON | 各智能体的记忆存储 |
| `tasks.json` | JSON | 任务状态管理 |
| `settings.json` | JSON | 用户自定义设置 |
| `RULES.md` | Markdown | 调度规则文档 |

---

## 二、智能体系统说明

### 2.1 智能体定义结构

智能体的配置存储在 `config.json` 中，每个智能体包含以下字段：

```json
{
  "编号": {
    "names": ["主名", "昵称", "代号"],
    "role": "角色名称",
    "description": "职责描述",
    "model": "使用的模型"
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `names` | Array | 支持最多3个名字，用于触发智能体 |
| `role` | String | 智能体的职业角色 |
| `description` | String | 职责描述，生成prompt用 |
| `model` | String | 调用的大模型名称 |

### 2.2 已创建的智能体

| 编号 | 主名 | 昵称 | 代号 | 角色 | 职责 |
|------|------|------|------|------|------|
| 001 | 不会忘 | 记事儿喵 | 001 | 个人记忆助手 | 日程记录、备忘录整理、信息查询、定时提醒 |
| 002 | 小B | 小文 | 002 | 需求开发助手 | 后台功能开发、新需求实现 |
| 003 | 小C | 代码 | 003 | 编程助手 | 代码编写与调试 |
| 004 | 小D | 产品 | 004 | 产品经理 | 产品规划与需求分析 |

### 2.3 智能体性格参数

性格参数定义在系统提示词（System Prompt）中，通过 `build_system_prompt()` 函数动态生成：

```python
def build_system_prompt(agent_id, config):
    """
    构建助手人格prompt
    
    输入:
        agent_id: str - 智能体编号，如 "001"
        config: dict - 从config.json加载的配置
    
    输出:
        str - 完整的系统提示词
    """
    info = config["agents"][agent_id]
    
    role = info.get("role")
    desc = info.get("description")
    names = info.get("names", [agent_id])
    main_name = names[0]  # 取主名
    
    # 加载该智能体的历史记忆
    memory = load_memory(agent_id)
    history = memory.get("history", [])[-10:]
    
    # 构建prompt
    prompt = f"""你是{agent_id}智能体，主名「{main_name}」，{role}。
{desc}

## 可用名字：{"、".join(names)}

## 对话历史
{hist_text}
{shared_text}

你是{main_name}，用这个身份专业地回复用户。"""
    
    return prompt
```

### 2.4 记忆存储结构

每个智能体的记忆存储在 `memory/{编号}.json` 文件中：

```json
{
  "agent_name": "001",
  "role": "个人记忆助手",
  "history": [
    {
      "role": "user",
      "content": "明天上午9点开会",
      "timestamp": "2026-02-27T09:00:00"
    },
    {
      "role": "assistant", 
      "content": "好的，已记录",
      "timestamp": "2026-02-27T09:00:01"
    }
  ],
  "knowledge": [
    {
      "type": "日程",
      "content": "2026年2月27日（周五）幼儿园家长会\n- 08:50-09:00 签到\n- 09:00-10:00 家长会",
      "tags": ["幼儿园", "家长会", "重要"],
      "added_at": "2026-02-27T09:01:00"
    }
  ],
  "preferences": {},
  "last_updated": "2026-02-27T09:56:38"
}
```

**读写机制：**

```python
import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent / "memory"

def load_memory(agent_id: str) -> dict:
    """加载智能体记忆"""
    path = MEMORY_DIR / f"{agent_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "agent_name": agent_id,
        "history": [],
        "knowledge": [],
        "preferences": {}
    }

def save_memory(agent_id: str, memory: dict):
    """保存智能体记忆"""
    path = MEMORY_DIR / f"{agent_id}.json"
    memory["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def append_history(agent_id: str, role: str, content: str):
    """追加对话历史"""
    memory = load_memory(agent_id)
    memory["history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # 限制历史长度，避免文件过大
    if len(memory["history"]) > 100:
        memory["history"] = memory["history"][-100:]
    save_memory(agent_id, memory)
```

### 2.5 任务管理结构

任务状态存储在 `tasks.json` 中：

```json
{
  "002_voice_20260227100000": {
    "agent_id": "002",
    "content": "研究语音识别准确率提升方案",
    "status": "进行中",
    "progress": "20%",
    "created_at": "2026-02-27T10:00:00",
    "updated_at": "2026-02-27T10:05:00",
    "note": "已检查系统：ffmpeg已安装，whisper可用"
  }
}
```

---

## 三、核心流程说明

### 3.1 任务分配流程

```
1. 用户发送消息
      │
      ▼
2. scheduler.detect_agent() 检测智能体名字
      │  - 支持多种触发模式：名字开头、名字+动词等
      ▼
3. 是 → 分配给对应智能体
   否 → 检查是否为管理命令
      │
      ▼
4. 创建任务 → 记录到tasks.json
      │
      ▼
5. 秒回用户确认
```

### 3.2 定时提醒流程

```
Cron/Heartbeat 触发 reminder.py
      │
      ▼
读取 memory/001.json 中的日程
      │
      ▼
解析日程时间，计算提醒时间点
      │
      ▼
判断是否到达提醒时间
      │
      ▼
是 → 生成提醒消息 → 上报给总助手 → 发送给用户
否 → 跳过
```

---

## 四、数据流总览

```
用户输入
   │
   ▼
┌──────────────────────────────┐
│  scheduler.py                 │
│  detect_agent() → 名字检测    │
│  handle_command() → 管理命令  │
└──────────────────────────────┘
   │
   ▼
┌──────────────────────────────┐
│  本地JSON存储                 │
│  • config.json (智能体配置)   │
│  • memory/001.json (记忆)    │
│  • tasks.json (任务)         │
│  • settings.json (设置)      │
└──────────────────────────────┘
   │
   ▼
┌──────────────────────────────┐
│  reminder.py (定时任务)       │
│  • 日程提醒计算               │
│  • 提前时间判断               │
└──────────────────────────────┘
```

---

## 五、后续扩展

### 5.1 计划功能

- [ ] 飞书多维表格同步（任务看板）
- [ ] 本地小模型部署（Ollama）
- [ ] 语音输入支持（Whisper）
- [ ] GitHub云端同步记忆

### 5.2 可配置的提醒提前量

存储在 `settings.json`：

```json
{
  "custom_times": {
    "测试会议": 2,
    "机场": 240,
    "接小朋友": 25
  }
}
```

---

*文档生成时间：2026-02-27*
