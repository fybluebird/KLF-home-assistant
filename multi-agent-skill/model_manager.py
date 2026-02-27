#!/usr/bin/env python3
"""
本地大模型自动更新与智力评估系统
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"

# 推荐的0.5b级别模型（按性能排序）
RECOMMENDED_MODELS = [
    {"name": "qwen:0.5b", "score": 85, "desc": "阿里千问0.5B，性价比高"},
    {"name": "phi:0.5b", "score": 82, "desc": "微软Phi-0.5B"},
    {"name": "qwen2:0.5b", "score": 88, "desc": "阿里千问2代0.5B，最新版"},
    {"name": "gemma:0.5b", "score": 80, "desc": "谷歌Gemma 0.5B"},
]

def get_current_model():
    """获取当前安装的模型"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            model_line = lines[1].split()
            return model_line[0] if model_line else None
    except:
        pass
    return None

def get_ollama_version():
    """检查Ollama版本"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "未安装"

def pull_model(model_name):
    """拉取新模型"""
    try:
        print(f"正在下载 {model_name}...")
        result = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def check_model_update():
    """检查模型更新"""
    current = get_current_model()
    print(f"当前模型: {current}")
    
    # 尝试更新到最新版本
    if current:
        model_name = current.split(":")[0]
        if pull_model(f"{model_name}:latest"):
            print(f"✅ {model_name} 已更新到最新版本")

def evaluate_model_intelligence():
    """评估模型智力水平"""
    prompt = """请评估以下方面的能力（0-100分）：
1. 逻辑推理能力
2. 语言理解能力  
3. 知识储备
4. 代码能力
5. 数学计算能力

请以JSON格式返回，格式如下：
{
  "逻辑推理": 85,
  "语言理解": 90,
  "知识储备": 75,
  "代码能力": 70,
  "数学计算": 60,
  "综合评分": 76
}"""

    try:
        result = subprocess.run(
            ["ollama", "run", "qwen:0.5b", prompt],
            capture_output=True, 
            text=True,
            timeout=120
        )
        
        # 尝试解析JSON结果
        output = result.stdout
        try:
            # 提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', output, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
        except:
            pass
        
        return {"raw_output": output[:500]}
    except Exception as e:
        return {"error": str(e)}

def generate_upgrade_suggestion(evaluation):
    """根据评估生成升级建议"""
    if "error" in evaluation:
        return "评估失败，无法生成建议"
    
    weak_points = []
    if evaluation.get("逻辑推理", 100) < 70:
        weak_points.append("逻辑推理")
    if evaluation.get("代码能力", 100) < 70:
        weak_points.append("代码能力")
    if evaluation.get("数学计算", 100) < 70:
        weak_points.append("数学计算")
    
    if weak_points:
        suggestion = f"建议升级到更大参数量模型（如qwen:1.8b或qwen:7b）以提升{', '.join(weak_points)}能力"
    else:
        suggestion = "当前模型表现良好，可继续使用"
    
    return suggestion

def save_evaluation(evaluation, suggestion):
    """保存评估结果到记忆"""
    memory_path = MEMORY_DIR / "evaluation.json"
    data = {
        "evaluation": evaluation,
        "suggestion": suggestion,
        "updated_at": datetime.now().isoformat()
    }
    
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 评估结果已保存")

def main():
    print("=" * 50)
    print("🧠 本地大模型智力评估系统")
    print("=" * 50)
    
    # 1. 检查更新
    print("\n[1/3] 检查模型更新...")
    check_model_update()
    
    # 2. 智力评估
    print("\n[2/3] 进行智力评估...")
    evaluation = evaluate_model_intelligence()
    print(f"评估结果: {evaluation}")
    
    # 3. 生成建议
    print("\n[3/3] 生成升级建议...")
    suggestion = generate_upgrade_suggestion(evaluation)
    print(f"建议: {suggestion}")
    
    # 保存
    save_evaluation(evaluation, suggestion)
    
    print("\n" + "=" * 50)
    print("✅ 评估完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
