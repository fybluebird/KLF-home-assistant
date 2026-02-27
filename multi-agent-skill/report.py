#!/usr/bin/env python3
"""
定时进度汇报脚本
每30分钟执行一次，检查任务状态并汇报
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

SKILL_DIR = Path(__file__).parent
TASKS_FILE = SKILL_DIR / "tasks.json"
LAST_REPORT_FILE = SKILL_DIR / ".last_report"

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def should_report():
    """检查是否需要汇报（每30分钟）"""
    if not LAST_REPORT_FILE.exists():
        return True
    
    with open(LAST_REPORT_FILE, "r") as f:
        last = datetime.fromisoformat(f.read().strip())
    
    # 30分钟间隔
    return (datetime.now() - last).total_seconds() >= 30 * 60

def mark_reported():
    with open(LAST_REPORT_FILE, "w") as f:
        f.write(datetime.now().isoformat())

def generate_report():
    tasks = load_tasks()
    active = {k: v for k, v in tasks.items() if v.get("status") == "进行中"}
    
    if not active:
        return None  # 无需汇报
    
    lines = ["📋 任务进度汇报："]
    for tid, t in active.items():
        lines.append(f"  • {t.get('agent')}: {t.get('content', '')[:30]}...")
        lines.append(f"    进度: {t.get('progress')} | 状态: {t.get('status')}")
    
    return "主人，小风现在给您汇报任务进度了～\n" + "\n".join(lines) + "\n～喵喵喵～\n进度汇报完毕，继续执行任务！"

if __name__ == "__main__":
    if should_report():
        report = generate_report()
        if report:
            print(report)
            mark_reported()
        else:
            print("NO_REPORT")  # 无任务时不打扰
    else:
        print("SKIP")
