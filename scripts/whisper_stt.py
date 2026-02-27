#!/usr/bin/env python3
"""
语音识别工具 - 使用 Faster Whisper
支持格式: WAV, MP3, FLAC, M4A, OGG (需要先转换)
"""

import sys
import os
import subprocess

# 设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

sys.path.insert(0, '/home/admin/.local/lib/python3.10/site-packages')

from faster_whisper import WhisperModel

MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        print("Loading whisper model...", file=sys.stderr)
        MODEL = WhisperModel('tiny', device='cpu', compute_type='int8')
        print("Model loaded!", file=sys.stderr)
    return MODEL

def convert_silk_to_wav(silk_path, wav_path):
    """转换 SILK 格式为 WAV (需要 silk_decoder)"""
    # 方法1: 使用 Python silk 模块
    try:
        import silk_decode
        silk_decode.decode(silk_path, wav_path)
        return True
    except:
        pass
    
    # 方法2: 尝试使用 ffmpeg (如果编译了 SILK 支持)
    result = subprocess.run(
        ['ffmpeg', '-i', silk_path, '-ar', '16000', '-ac', '1', wav_path, '-y'],
        capture_output=True
    )
    return result.returncode == 0

def transcribe(audio_path):
    """识别音频文件"""
    # 检查文件类型
    ext = os.path.s.path.splitext(audio_path)[1].lower()
    
    # 如果是 SILK 格式，尝试转换
    if ext in ['.silk', '.amr'] and b'SILK' in open(audio_path, 'rb').read(20):
        print("检测到 SILK 格式，需要转换...", file=sys.stderr)
        wav_path = '/tmp/silk_converted.wav'
        if convert_silk_to_wav(audio_path, wav_path):
            audio_path = wav_path
        else:
            return "[错误: SILK 格式需要解码器，当前无法处理]"
    
    model = load_model()
    segments, info = model.transcribe(audio_path, language='zh')
    
    result = []
    for segment in segments:
        result.append(segment.text)
    
    return ''.join(result)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 whisper_stt.py <audio_file>", file=sys.stderr)
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}", file=sys.stderr)
        sys.exit(1)
    
    text = transcribe(audio_file)
    print(text)
