"""測試 Faster-Whisper 模型載入與基本辨識"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from faster_whisper import WhisperModel
import numpy as np

print("正在載入 Faster-Whisper base 模型 (首次會下載約 140MB)...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("模型載入成功！")

audio = np.zeros(16000 * 3, dtype=np.float32)
segments, _ = model.transcribe(audio, language="zh")
text = "".join([s.text for s in segments])
print(f"測試辨識結果: '{text}'")
print("[OK] Faster-Whisper 整合測試通過")
