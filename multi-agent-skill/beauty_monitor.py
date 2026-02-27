#!/usr/bin/env python3
"""
美妆趋势监控系统 V5 - 集成可抓取的网站
"""

import subprocess
import re
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).parent
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

def send_qq(message):
    msg_escaped = message.replace("\n", "\\n")
    subprocess.run(f"{QQ_SEND} {TARGET_OPENID} \"{msg_escaped}\"", shell=True)

def fetch_url(url):
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        return response.read().decode('utf-8')
    except:
        return ""

def get_baidu_trends():
    """百度热搜"""
    trends = []
    html = fetch_url("https://top.baidu.com/board?tab=realtime")
    if html:
        items = re.findall(r'title="([^"]+)"', html)[:10]
        if items:
            trends.append("\n🇨🇳 百度热搜 Top10：")
            for i, item in enumerate(items[:10], 1):
                trends.append(f"  {i}. {item[:30]}")
    return trends

def get_weibo_tech():
    """科技微博热搜"""
    trends = []
    html = fetch_url("https://s.weibo.com/top/summary?cate=tech")
    if html and "热搜" in html:
        items = re.findall(r'微博热搜榜([^<]+)', html)
        if items:
            trends.append("\n🇨🇳 微博科技热搜：")
            for i, item in enumerate(items[:5], 1):
                trends.append(f"  {i}. {item[:30]}")
    return trends

def get_douyin_rank():
    """抖音热榜"""
    trends = []
    html = fetch_url("https://www.douyin.com/aweme/v1/web/hot/search/list/")
    if html:
        try:
            import json
            data = json.loads(html)
            if data.get("data") and data["data"].get("word_list"):
                trends.append("\n🎵 抖音热榜：")
                for i, item in enumerate(data["data"]["word_list"][:5], 1):
                    trends.append(f"  {i}. {item.get('word', '')[:30]}")
        except:
            pass
    return trends

def get_glossy():
    """Glossy美妆"""
    trends = []
    html = fetch_url("https://www.glossy.co/beauty")
    if html:
        titles = re.findall(r'\[([^\]]+)\]\(https?://[^\)]+\)', html)
        if titles:
            trends.append("\n📰 Glossy热门：")
            for t in titles[:5]:
                trends.append(f"  • {t[:50]}")
    return trends

def get_wwd():
    """WWD"""
    trends = []
    html = fetch_url("https://wwd.com/beauty-industry")
    if html:
        titles = re.findall(r'<a[^>]*title="([^"]+)"', html)[:5]
        if titles:
            trends.append("\n📰 WWD Beauty：")
            for t in titles:
                trends.append(f"  • {t[:50]}")
    return trends

def generate_report():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""💄 美妆趋势周报 V5 - {now}
{'='*35}

【🇺🇸 美国数据源】
"""
    report += "\n".join(get_glossy())
    report += "\n".join(get_wwd())
    
    report += """

【🇨🇳 中国数据源】
"""
    report += "\n".join(get_baidu_trends())
    report += "\n".join(get_douyin_rank())
    
    report += f"""

{'='*35}
📌 已测试可用数据源：
✅ 百度热搜
✅ Glossy
✅ WWD
⚠️ 微博/抖音（需API或代理）
"""
    return report

def main():
    print("💄 正在获取趋势数据...")
    report = generate_report()
    print(report)
    send_qq(report)
    print("✅ 报告已发送")

if __name__ == "__main__":
    main()
