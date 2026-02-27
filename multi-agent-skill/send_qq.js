#!/usr/bin/env node
/**
 * QQ机器人主动消息推送脚本 v3
 */

const API_BASE = "https://api.sgroup.qq.com";
const TOKEN_URL = "https://bots.qq.com/app/getAppAccessToken";

const fs = require("fs");
const config = JSON.parse(fs.readFileSync("/home/admin/.openclaw/openclaw.json", "utf8"));
const qqbotConfig = config.channels?.qqbot;

if (!qqbotConfig) {
  console.error("❌ 未找到QQ机器人配置");
  process.exit(1);
}

const APP_ID = qqbotConfig.appId;
const CLIENT_SECRET = qqbotConfig.clientSecret;

let cachedToken = null;

// 获取Access Token
async function getAccessToken() {
  if (cachedToken) return cachedToken;

  const response = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appId: APP_ID, clientSecret: CLIENT_SECRET })
  });

  const data = await response.json();
  if (data.access_token) {
    cachedToken = data.access_token;
    return cachedToken;
  }
  throw new Error("获取Token失败: " + JSON.stringify(data));
}

// 发送C2C消息
async function sendC2CMessage(targetOpenId, content) {
  const token = await getAccessToken();
  
  const url = `${API_BASE}/v2/users/${targetOpenId}/messages`;
  
  console.log(`📤 发送中...`);
  
  try {
    // 正确的API格式（纯文本模式）
    const body = {
      content: content,
      msg_type: 0,
      msg_seq: 1
    };
    
    console.log("请求体:", JSON.stringify(body));
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `QQBot ${token}`
      },
      body: JSON.stringify(body)
    });
    
    const result = await response.json();
    console.log("📬 结果:", JSON.stringify(result, null, 2));
    
    if (result.ret === 0) {
      console.log("✅ 发送成功!");
      return true;
    } else {
      console.log("❌ 失败:", result);
      return false;
    }
  } catch (e) {
    console.error("❌ 错误:", e.message);
    return false;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const target = args[0] || "352983D4C8F36D56E350266944DF8DE1";
  const message = args.slice(1).join(" ") || "测试消息";
  
  await sendC2CMessage(target, message);
}

main();
