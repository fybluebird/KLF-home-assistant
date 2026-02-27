#!/usr/bin/env python3
"""
QQ 语音识别 - SILK -> WAV -> Whisper
"""

import os
import sys
import subprocess

# 设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

SILK_DECODER = '/home/admin/silk-v3-decoder/silk/decoder'
MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        print("Loading whisper model...", file=sys.stderr)
        from faster_whisper import WhisperModel
        MODEL = WhisperModel('tiny', device='cpu', compute_type='int8')
        print("Model loaded!", file=sys.stderr)
    return MODEL

def silk_to_wav(silk_path, wav_path):
    """转换 SILK 到 WAV"""
    pcm_path = wav_path.replace('.wav', '.pcm')
    
    # 1. SILK -> PCM
    result = subprocess.run(
        [SILK_DECODER, silk_path, pcm_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, f"Decoder error: {result.stderr}"
    
    # 2. PCM -> WAV
    result = subprocess.run(
        ['ffmpeg', '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', pcm_path, wav_path, '-y'],
        capture_output=True, text=True
    )
    
    # 清理 PCM
    if os.path.exists(pcm_path):
        os.remove(pcm_path)
    
    return result.returncode == 0, "OK"

def transcribe(wav_path):
    """识别 WAV 文件"""
    model = load_model()
    segments, info = model.transcribe(wav_path, language='zh')
    return ''.join([s.text for s in segments])

def recognize_silk(silk_path):
    """识别 SILK 文件"""
    wav_path = '/tmp/silk_recognized.wav'
    
    # 转换
    ok, msg = silk_to_wav(silk_path, wav_path)
    if not ok:
        return f"转换失败: {msg}"
    
    # 识别
    return transcribe(wav_path)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 qq_voice_recognize.py <silk_file>")
        sys.exit(1)
    
    result = recognize_silk(sys.argv[1])
    print(result)
