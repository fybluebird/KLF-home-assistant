#!/usr/bin/env python3
"""
家庭助手 - 语音对话Demo
功能：语音输入 -> 识别 -> 对话 -> 语音输出
"""

import subprocess
import json
import sys

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def voice_input():
    """语音输入（暂用文本模拟）"""
    print("请说话（输入文本）: ", end="")
    return input()

def speech_to_text(audio_path=None):
    """语音识别 - 用Whisper"""
    if audio_path:
        cmd = f'whisper "{audio_path}" --language Chinese --model base'
    else:
        # 测试用默认音频
        cmd = 'echo "测试语音识别"'
    return run_command(cmd)

def chat_with_ai(text):
    """对话 - 用本地Ollama"""
    cmd = f'echo "{text}" | ollama run qwen:0.5b'
    response = run_command(cmd)
    return response

def text_to_speech(text):
    """语音合成 - 用Ollama或其他TTS"""
    # 暂用命令行输出模拟
    print(f"🎤 回复: {text}")

def main():
    print("=" * 50)
    print("🏠 家庭助手 - 语音对话Demo")
    print("=" * 50)
    
    # 1. 语音输入
    print("\n🎤 请说话...")
    text = voice_input()
    if not text:
        text = "你好"
    
    # 2. 语音识别
    print("🧠 识别中...")
    # recognized_text = speech_to_text()  # 暂用直接输入
    recognized_text = text
    print(f"   识别结果: {recognized_text}")
    
    # 3. AI对话
    print("💬 对话中...")
    response = chat_with_ai(recognized_text)
    
    # 4. 语音输出
    print(f"🎤 回复: {response}")
    
    print("\n✅ 对话完成！")

if __name__ == "__main__":
    main()
