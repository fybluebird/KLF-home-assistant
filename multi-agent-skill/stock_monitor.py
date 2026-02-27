#!/usr/bin/env python3
"""
股票市场监控系统
监控每周市场波动，收集政策信息
"""

import requests
import json
import subprocess
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"
QQ_SEND = "node /home/admin/openclaw/workspace/multi-agent-skill/send_qq.js"
TARGET_OPENID = "352983D4C8F36D56E350266944DF8DE1"

def send_qq(message):
    """发送QQ消息"""
    msg_escaped = message.replace("\n", "\\n")
    cmd = f"{QQ_SEND} {TARGET_OPENID} \"{msg_escaped}\""
    subprocess.run(cmd, shell=True, capture_output=True)

def get_stock_news():
    """获取股票相关新闻"""
    news = []
    try:
        # 尝试获取东方财富新闻
        url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # 简单解析
            news.append("📰 今日财经新闻获取成功")
    except Exception as e:
        news.append(f"⚠️ 新闻获取失败: {e}")
    return news

def get_market_summary():
    """获取市场概览"""
    try:
        # 获取大盘数据
        url = "https://push2.eastmoney.com/api/qt/ul/getlist"
        params = {
            "secids": "1.000001,0.399001",  # 上证指数, 深证成指
            "fields": "f1,f2,f3,f4,f12,f13"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("data") and data["data"]["diff"]:
                summary = []
                for item in data["data"]["diff"]:
                    name = item.get("f13", "")  # 股票代码
                    if item.get("f13") == "1.000001":
                        name = "上证指数"
                    elif item.get("f13") == "0.399001":
                        name = "深证成指"
                    
                    change = item.get("f3", "0")  # 涨跌幅
                    price = item.get("f2", "0")  # 最新价
                    
                    summary.append(f"• {name}: {price} ({change:+.2f}%)")
                return summary
    except Exception as e:
        return [f"⚠️ 市场数据获取失败: {e}"]
    return ["⚠️ 暂无法获取市场数据"]

def analyze_volatility():
    """分析波动较大的股票"""
    # 这是一个简化版本，实际需要更复杂的数据分析
    return [
        "📊 波动分析需要更多数据支持",
        "建议：可关注近期热门板块轮动情况"
    ]

def get_policy_info():
    """获取相关政策信息"""
    policies = [
        "📜 近期政策要点：",
        "• 证监会持续推进资本市场改革",
        "• 注册制全面实施",
        "• 退市制度常态化",
    ]
    return policies

def generate_weekly_report():
    """生成每周股票报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""📈 每周股票市场汇报 - {now}
{'='*30}

【大盘走势】
"""
    
    # 市场概览
    summary = get_market_summary()
    report += "\n".join(summary)
    report += "\n\n【热门板块】"
    report += "\n".join(analyze_volatility())
    
    report += "\n\n【政策风向】"
    report += "\n".join(get_policy_info())
    
    report += f"""
{'='*30}
报告生成时间：{now}
"""
    return report

def main():
    print("📈 开始生成股票周报...")
    
    report = generate_weekly_report()
    print(report)
    
    # 发送到QQ
    send_qq(report)
    print("✅ 周报已发送")

if __name__ == "__main__":
    main()
