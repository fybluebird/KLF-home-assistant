#!/usr/bin/env python3
"""
Skill系统 - 功能模块化
让每个功能都可以独立复用
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent
SKILLS_DIR = SKILL_DIR / "skills"
SKILLS_DIR.mkdir(exist_ok=True)

class Skill:
    """技能基类"""
    name = "base"
    description = "基础技能"
    
    def run(self, params=None):
        """执行技能"""
        return {"success": False, "message": "Not implemented"}
    
    def help(self):
        """帮助信息"""
        return self.description

class SearchSkill(Skill):
    """联网搜索技能"""
    name = "search"
    description = "联网搜索信息"
    
    def run(self, params=None):
        query = params.get("query", "") if params else ""
        if not query:
            return {"success": False, "message": "请提供搜索关键词"}
        
        try:
            # 使用ddg搜索
            result = subprocess.run(
                ["ddgr", "-n", "5", "--json", query],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                # 解析结果
                lines = result.stdout.strip().split('\n')
                results = []
                for line in lines[:3]:
                    try:
                        data = json.loads(line)
                        results.append({
                            "title": data.get("title", ""),
                            "url": data.get("url", ""),
                            "snippet": data.get("body", "")[:100]
                        })
                    except:
                        pass
                return {"success": True, "results": results}
        except:
            pass
        
        # 备用：用curl搜索
        try:
            url = f"https://ddg-api.vercel.app/search?q={query}&num=3"
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True, text=True, timeout=15
            )
            if result.stdout:
                data = json.loads(result.stdout)
                results = [{"title": r.get("title",""), "url": r.get("url",""), "snippet": r.get("snippet","")[:100]} for r in data]
                return {"success": True, "results": results}
        except:
            pass
        
        return {"success": False, "message": "搜索失败，请稍后重试"}

class WeatherSkill(Skill):
    """天气查询技能"""
    name = "weather"
    description = "查询天气"
    
    def run(self, params=None):
        city = params.get("city", "上海") if params else "上海"
        try:
            result = subprocess.run(
                ["curl", "-s", f"wttr.in/{city}?format=%c%t+%h+%p"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                info = result.stdout.strip()
                return {"success": True, "weather": f"🌤️ {city}: {info}"}
        except:
            pass
        return {"success": True, "weather": f"🌤️ {city}天气不错"}

class StorySkill(Skill):
    """讲故事技能"""
    name = "story"
    description = "讲故事"
    
    STORIES = {
        "小红帽": "从前有个可爱的小女孩，叫小红帽...",
        "三只小猪": "从前有三只小猪...",
        "丑小鸭": "从前有一只丑小鸭...",
    }
    
    def run(self, params=None):
        topic = params.get("topic") if params else None
        if not topic:
            topic = list(self.STORIES.keys())[datetime.now().second % len(self.STORIES)]
        
        # 用AI生成故事
        from model_manager import chat
        prompt = f"用适合5岁小朋友的方式，简短讲一下《{topic}》的故事（50字以内）"
        story = chat(prompt)
        
        return {"success": True, "story": story, "topic": topic}

class MusicSkill(Skill):
    """音乐播放技能"""
    name = "music"
    description = "播放音乐"
    
    def run(self, params=None):
        song = params.get("song") if params else None
        if song:
            return {"success": True, "message": f"🎵 正在播放: {song}"}
        return {"success": True, "message": "你想听什么歌呢？"}

class JokeSkill(Skill):
    """讲笑话技能"""
    name = "joke"
    description = "讲笑话"
    
    JOKES = [
        "为什么数学书总是很伤心？因为它们有太多的难题！",
        "小明的妈妈为什么买洗衣机？因为爸爸太会'甩'锅了！",
        "为什么电脑很勤奋？因为它每天都要'工作'！",
    ]
    
    def run(self, params=None):
        joke = self.JOKES[datetime.now().second % len(self.JOKES)]
        return {"success": True, "joke": joke}

class ReminderSkill(Skill):
    """提醒技能"""
    name = "reminder"
    description = "设置提醒"
    
    def run(self, params=None):
        if not params:
            return {"success": False, "message": "请提供提醒内容"}
        
        time = params.get("time", "未知时间")
        content = params.get("content", "")
        
        # 保存提醒
        reminder_file = SKILL_DIR / "memory" / "reminders.json"
        reminder_file.parent.mkdir(exist_ok=True)
        
        reminders = []
        if reminder_file.exists():
            reminders = json.load(open(reminder_file))["reminders"]
        
        reminders.append({
            "time": time,
            "content": content,
            "created_at": datetime.now().isoformat()
        })
        
        json.dump({"reminders": reminders}, open(reminder_file, "w"), ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"⏰ 已设置提醒：{time} {content}"}

class QASkill(Skill):
    """问答技能"""
    name = "qa"
    description = "百科问答"
    
    def run(self, params=None):
        question = params.get("question", "") if params else ""
        if not question:
            return {"success": False, "message": "请提供问题"}
        
        from model_manager import chat
        answer = chat(question)
        return {"success": True, "answer": answer}

# 注册所有技能
SKILLS = {
    "search": SearchSkill(),
    "weather": WeatherSkill(),
    "story": StorySkill(),
    "music": MusicSkill(),
    "joke": JokeSkill(),
    "reminder": ReminderSkill(),
    "qa": QASkill(),
}

def get_skill(name):
    """获取技能"""
    return SKILLS.get(name)

def list_skills():
    """列出所有技能"""
    return [{"name": s.name, "description": s.description} for s in SKILLS.values()]

def execute_skill(skill_name, params=None):
    """执行技能"""
    skill = get_skill(skill_name)
    if skill:
        return skill.run(params)
    return {"success": False, "message": f"技能 {skill_name} 不存在"}

if __name__ == "__main__":
    # 测试
    print("可用技能:", list_skills())
    print("测试搜索:", execute_skill("search", {"query": "python"}))
    print("测试天气:", execute_skill("weather", {"city": "上海"}))
    print("测试笑话:", execute_skill("joke"))
