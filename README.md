# 🏠 家庭管家系统

> 基于 OpenClaw 的多智能体家庭助手

## 功能特点

- 🤖 多智能体协作（001-006）
- 📊 网页控制面板
- 💬 QQ机器人集成
- ⏰ 定时任务提醒
- 🧠 记忆系统

## 快速开始

```bash
# 安装依赖
pip3 install flask psutil

# 启动仪表盘
cd multi-agent-skill
python3 dashboard.py

# 启动任务执行器
python3 task_executor.py
```

## 智能体

| 编号 | 名称 | 职责 |
|------|------|------|
| 001 | 不会忘 | 日程记忆 |
| 002 | 小B | 需求开发 |
| 003 | 小C | 编程助手 |
| 004 | 小D | 产品经理 |
| 005 | 小股 | 股票监控 |
| 006 | 小美 | 美妆趋势 |

## 部署

详见 [部署文档](docs/DEPLOY.md)

## License

MIT
