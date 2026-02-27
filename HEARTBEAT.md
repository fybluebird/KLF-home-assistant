# HEARTBEAT.md

# 定时任务检查

## 1. 检查任务进度（每30分钟）

当收到心跳时，执行以下检查：

1. 读取 `multi-agent-skill/tasks.json`
2. 检查是否有"进行中"的任务
3. 如果有，生成汇报消息发送给用户

**汇报格式：**
```
主人，小风现在给您汇报任务进度了～
📋 任务进度汇报：
  • 任务名... [进度] [状态]
～喵喵喵～
进度汇报完毕，继续执行任务！
```

## 2. 检查日程提醒

执行 `cd /home/admin/openclaw/workspace/multi-agent-skill && python3 reminder.py check`

如果输出不是 "NO_REMINDER"，则生成提醒消息发送给用户。

## 3. 无任务时

如果没有进行中的任务，也没有提醒，则回复 HEARTBEAT_OK
