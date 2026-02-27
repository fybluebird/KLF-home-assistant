#!/usr/bin/env python3
"""
QQ机器人图片监听器
监听接收到的图片并自动保存
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 配置
QQBOT_DIR = Path.home() / ".openclaw" / "extensions" / "qqbot"
SAVE_DIR = Path.home() / "openclaw_workspace" / "received_images"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 图片保存目录: {SAVE_DIR}")
print("🪐 开始监听图片消息...")

def download_image(image_url, filename):
    """下载图片"""
    try:
        # 使用curl下载
        result = subprocess.run(
            ["curl", "-L", "-o", str(SAVE_DIR / filename), image_url],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ 下载成功: {filename}")
            return True
        else:
            print(f"❌ 下载失败: {filename}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def check_for_images():
    """检查是否有新图片"""
    # 检查qqbot的缓存目录
    cache_dirs = [
        QQBOT_DIR / "data",
        QQBOT_DIR / "cache",
        QQBOT_DIR / "runtime",
    ]
    
    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue
        
        # 查找图片文件
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"]:
            for img_file in cache_dir.rglob(ext):
                # 检查是否是最近创建的（1小时内）
                if time.time() - img_file.stat().st_mtime < 3600:
                    print(f"🖼️ 发现图片: {img_file.name}")
                    
                    # 复制到保存目录
                    new_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{img_file.name}"
                    try:
                        import shutil
                        shutil.copy2(img_file, SAVE_DIR / new_name)
                        print(f"✅ 已保存: {new_name}")
                    except Exception as e:
                        print(f"❌ 保存失败: {e}")

def main():
    """主循环"""
    while True:
        try:
            check_for_images()
        except Exception as e:
            print(f"❌ 监听错误: {e}")
        
        time.sleep(10)  # 每10秒检查一次

if __name__ == "__main__":
    main()
