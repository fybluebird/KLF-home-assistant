#!/usr/bin/env python3
"""
家庭助手 - 模型管理器
支持本地+云端多种模型
"""

import os
import subprocess
import json
from pathlib import Path

# 配置文件
CONFIG_FILE = Path(__file__).parent / "model_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "current_model": "ollama",  # 当前使用的模型
    "ollama": {
        "enabled": True,
        "model": "qwen:0.5b",
        "endpoint": "http://localhost:11434"
    },
    "openai": {
        "enabled": False,
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "endpoint": "https://api.openai.com/v1"
    },
    "qwen": {
        "enabled": False,
        "api_key": "",
        "model": "qwen-turbo",
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "ernie": {
        "enabled": False,
        "api_key": "",
        "model": "ernie-4.0-8k",
        "endpoint": "https://qianfan.baidubce.com/v2"
    }
}

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def chat(text, model=None):
    """通用对话接口"""
    config = load_config()
    
    # 选择模型
    if model:
        config["current_model"] = model
    
    current = config["current_model"]
    
    # 优先使用启用的模型
    if current == "ollama" and config["ollama"]["enabled"]:
        return chat_ollama(text, config["ollama"])
    elif current == "openai" and config["openai"]["enabled"]:
        return chat_openai(text, config["openai"])
    elif current == "qwen" and config["qwen"]["enabled"]:
        return chat_qwen(text, config["qwen"])
    elif current == "ernie" and config["ernie"]["enabled"]:
        return chat_ernie(text, config["ernie"])
    else:
        # 回退到本地Ollama
        return chat_ollama(text, config["ollama"])

def chat_ollama(text, config):
    """本地Ollama"""
    try:
        result = subprocess.run(
            ["ollama", "run", config["model"], text],
            capture_output=True, text=True, timeout=60
        )
        return {
            "success": True,
            "reply": result.stdout.strip() if result.stdout else "抱歉，我没有听清楚",
            "model": config["model"]
        }
    except Exception as e:
        return {
            "success": False,
            "reply": f"本地模型出错: {str(e)[:50]}",
            "model": "ollama"
        }

def chat_openai(text, config):
    """OpenAI API"""
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config["model"],
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 500
        }
        resp = requests.post(
            f"{config['endpoint']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = resp.json()
        return {
            "success": True,
            "reply": result["choices"][0]["message"]["content"],
            "model": config["model"]
        }
    except Exception as e:
        return {
            "success": False,
            "reply": f"API出错: {str(e)[:50]}",
            "model": "openai"
        }

def chat_qwen(text, config):
    """阿里通义千问"""
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config["model"],
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 500
        }
        resp = requests.post(
            f"{config['endpoint']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = resp.json()
        return {
            "success": True,
            "reply": result["choices"][0]["message"]["content"],
            "model": config["model"]
        }
    except Exception as e:
        return {
            "success": False,
            "reply": f"API出错: {str(e)[:50]}",
            "model": "qwen"
        }

def chat_ernie(text, config):
    """百度文心一言"""
    try:
        import requests
        # 获取access_token (简化版，实际需要OAuth)
        # 这里假设已经有api_key
        headers = {"Content-Type": "application/json"}
        data = {
            "model": config["model"],
            "messages": [{"role": "user", "content": text}],
            "max_output_tokens": 500
        }
        resp = requests.post(
            f"{config['endpoint']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = resp.json()
        return {
            "success": True,
            "reply": result["choices"][0]["message"]["content"],
            "model": config["model"]
        }
    except Exception as e:
        return {
            "success": False,
            "reply": f"API出错: {str(e)[:50]}",
            "model": "ernie"
        }

def switch_model(model_name):
    """切换模型"""
    config = load_config()
    if model_name in config:
        config["current_model"] = model_name
        save_config(config)
        return True
    return False

def get_status():
    """获取模型状态"""
    config = load_config()
    return {
        "current": config["current_model"],
        "available": [k for k in ["ollama", "openai", "qwen", "ernie"] if config[k]["enabled"]],
        "config": config
    }

if __name__ == "__main__":
    # 测试
    print("模型状态:", get_status())
    print("测试对话:", chat("你好"))
