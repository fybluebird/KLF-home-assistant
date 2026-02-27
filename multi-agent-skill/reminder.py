#!/usr/bin/env python3
"""
定时提醒系统
- 每天8:30发送当天日程
- 日程前自动提醒
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"
CONFIG_FILE = SKILL_DIR / "config.json"
REMINDERS_FILE = SKILL_DIR / ".reminders"  # 已提醒记录
SETTINGS_FILE = SKILL_DIR / "settings.json"  # 用户设置（提前时间等）

# 默认提前提醒时间（分钟）
DEFAULT_REMINDERS = {
    "机场": 240,        # 4小时
    "接小朋友": 25,    # 25分钟（路程10+缓冲）
    "开会": 15,
    "上课": 15,
    "家长会": 30,
    "默认": 30
}

def load_memory(agent_id="001"):
    path = MEMORY_DIR / f"{agent_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"knowledge": []}

def load_settings():
    if Path(SETTINGS_FILE).exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"custom_times": {}}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def parse_time(time_str):
    """解析时间字符串，如 '09:00', '15:00' """
    try:
        return datetime.strptime(time_str.strip(), "%H:%M").time()
    except:
        return None

def get_reminder_minutes(content, settings):
    """判断提前提醒时间"""
    content_lower = content.lower()
    
    # 检查自定义设置
    for key, minutes in settings.get("custom_times", {}).items():
        if key in content_lower:
            return minutes
    
    # 默认规则
    for keyword, minutes in DEFAULT_REMINDERS.items():
        if keyword in content_lower:
            return minutes
    
    return DEFAULT_REMINDERS["默认"]

def get_today_schedule():
    """获取今天和未来的日程"""
    import re
    memory = load_memory("001")
    now = datetime.now()
    today = now.date()
    
    schedules = []
    
    for item in memory.get("knowledge", []):
        if item.get("type") == "日程":
            content = item.get("content", "")
            
            # 解析日期
            date_match = re.search(r'(\d+)年(\d+)月(\d+)日', content)
            if not date_match:
                continue
            
            year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
            schedule_date = datetime(year, month, day).date()
            
            # 只处理今天及未来的
            if schedule_date < today:
                continue
            
            # 提取时间点
            times = re.findall(r'(\d{1,2}:\d{2})[-–]?', content)
            seen = set()
            for t in times:
                if t in seen:
                    continue
                seen.add(t)
                
                time_obj = parse_time(t)
                if time_obj:
                    dt = datetime.combine(schedule_date, time_obj)
                    if dt > now or schedule_date == today:  # 今天的也显示
                        schedules.append({
                            "time": dt,
                            "content": content.split('\n')[0],  # 第一行是日期标题
                            "full_content": content,
                            "reminder_minutes": get_reminder_minutes(content, load_settings())
                        })
    
    return sorted(schedules, key=lambda x: x["time"])

def check_reminders():
    """检查是否需要提醒"""
    now = datetime.now()
    schedules = get_today_schedule()
    
    # 加载已提醒记录
    reminded = set()
    if Path(REMINDERS_FILE).exists():
        with open(REMINDERS_FILE, "r") as f:
            reminded = set(json.load(f))
    
    messages = []
    
    for s in schedules:
        reminder_time = s["time"] - timedelta(minutes=s["reminder_minutes"])
        
        # 还没到提醒时间，或者已经提醒过了
        if now < reminder_time:
            continue
        
        # 检查是否已提醒（用时间戳做key）
        key = f"{s['time'].isoformat()}"
        if key in reminded:
            continue
        
        # 生成提醒消息
        minutes_until = int((s["time"] - now).total_seconds() / 60)
        
        if minutes_until <= 0:
            msg = f"⏰ 现在开始：{s['content']}"
        else:
            msg = f"⏰ 即将开始（{minutes_until}分钟后）：{s['content']}"
        
        messages.append(msg)
        
        # 记录已提醒
        reminded.add(key)
    
    # 保存提醒记录
    with open(REMINDERS_FILE, "w") as f:
        json.dump(list(reminded), f)
    
    return messages

def daily_schedule_message():
    """生成每日日程消息"""
    now = datetime.now()
    schedules = get_today_schedule()
    
    lines = [f"📋 今日日程 - {now.strftime('%Y年%m月%d日 %H:%M')}", ""]
    
    if not schedules:
        lines.append("  今日暂无日程安排")
    else:
        current_date = None
        for s in schedules:
            dt = s["time"]
            time_str = dt.strftime("%H:%M")
            
            # 新日期标题
            if dt.date() != current_date:
                current_date = dt.date()
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
                lines.append(f"\n📅 {dt.month}月{dt.day}日（{weekday}）")
            
            lines.append(f"  ⏰ {time_str} - {s['content']}")
    
    lines.append("")
    lines.append("💡 如有需要设定提前提醒时间的日程，请告诉我具体时间～")
    
    return "\n".join(lines)
    
    if not has_schedule:
        lines.append("  今日暂无日程安排")
    
    # 检查是否需要询问提前时间
    lines.append("")
    lines.append("💡 如有需要设定提前提醒时间的日程，请告诉我具体时间～")
    
    return "\n".join(lines)

# CLI测试
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check", "daily", "set"])
    parser.add_argument("--time", type=int, help="提前分钟数")
    parser.add_argument("--keyword", help="关键词")
    args = parser.parse_args()
    
    if args.action == "check":
        msgs = check_reminders()
        if msgs:
            for m in msgs:
                print(m)
        else:
            print("NO_REMINDER")
    
    elif args.action == "daily":
        print(daily_schedule_message())
    
    elif args.action == "set":
        if args.keyword and args.time:
            settings = load_settings()
            settings["custom_times"][args.keyword] = args.time
            save_settings(settings)
            print(f"✅ 已设定：{args.keyword} 提前 {args.time} 分钟提醒")
        else:
            print("用法: --set --keyword 关键词 --time 分钟数")
