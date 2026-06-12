"""驗證音訊前處理不會造成錯誤"""
import numpy as np

raw = np.random.randn(16000).astype(np.float32) * 0.1

raw = np.append(raw[0], raw[1:] - 0.97 * raw[:-1])
rms = np.sqrt(np.mean(np.square(raw)))
if rms > 0:
    raw = raw / rms * 0.12

print(f"min={raw.min():.4f} max={raw.max():.4f} rms={np.sqrt(np.mean(np.square(raw))):.4f}")
print("[OK] 音訊前處理正常")
