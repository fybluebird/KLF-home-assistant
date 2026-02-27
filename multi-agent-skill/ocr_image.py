#!/usr/bin/env python3
"""
在线OCR - 使用免费的OCR.space API
"""

import base64
import requests
import sys
import json

def ocr_image(image_path_or_url):
    """OCR识别图片文字"""
    
    # 如果是URL直接用URL
    if image_path_or_url.startswith("http"):
        url = "https://api.ocr.space/parse/image"
        payload = {"url": image_path_or_url, "language": "chs"}
    else:
        # 本地图片转base64
        with open(image_path_or_url, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        url = "https://api.ocr.space/parse/imagebase64"
        payload = {"base64Image": f"data:image/jpeg;base64,{img_base64}", "language": "chs"}
    
    # 免费API，不需要key（但有频率限制）
    headers = {"apikey": "helloworld"}
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        result = response.json()
        
        if result.get("ParsedResults"):
            text = result["ParsedResults"][0]["ParsedText"]
            return text
        else:
            return f"识别失败: {result}"
    except Exception as e:
        return f"错误: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 ocr_image.py <图片路径或URL>")
        sys.exit(1)
    
    result = ocr_image(sys.argv[1])
    print(result)
