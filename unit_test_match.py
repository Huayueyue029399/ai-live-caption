"""單元測試：驗證 match_lyrics 校正功能"""
import json
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from pro_caption_app import UltimateRealTimeCaptionApp
import tkinter as tk

with open("lyrics_lines.json", "r", encoding="utf-8") as f:
    lyrics_lines = json.load(f)

root = tk.Tk()
app = UltimateRealTimeCaptionApp(root)
app.lyrics_lines = lyrics_lines

test_cases = [
    ("天黑的時候 影子都會離開", "天黑的時候 連影子都會離開"),
    ("所以我想問 到底什麼才是愛", "所以我想問 到底什麼才是愛"),
    ("短暫的幸福總在這快餐時代", "短暫的幸福總在這快餐時代"),
    ("長情的人格格不入般存在", "長情的人格格不入般存在"),
    ("後來才明白 例外並不代表偏愛", "後來才明白 例外並不代表偏愛"),
    ("請記住我的好 或者記住我就好", "請記住我的好 或者記住我就好"),
    ("別離開好不好", "別離開好不好 沒你的日子真的很難熬"),
    ("我的心在下雨 天怎麼會晴", "如果你的心裡面在下雨 天怎麼會晴"),
    ("愛上你我傷了多少次心", "愛上你我傷了多少次心 受多少委屈"),
]

print(f"{'='*60}")
print(f" match_lyrics 校正測試")
print(f"{'='*60}")

passed = 0
total = len(test_cases)
for vosk_input, expected in test_cases:
    result = app.match_lyrics(vosk_input)
    match = result == expected or vosk_input == expected
    status = "OK" if match else "FAIL"
    if match:
        passed += 1
    print(f"  [{status}] Vosk: {vosk_input[:30]}")
    print(f"         輸出: {result[:35]}")
    print(f"         期望: {expected[:35]}")
    print()

accuracy = (passed / total * 100) if total > 0 else 0
print(f"{'='*60}")
print(f" 通過: {passed}/{total} ({accuracy:.1f}%)")
if accuracy >= 80:
    print(f" [OK] 已達目標 80%！")
else:
    print(f" [..] 未達 80%，需繼續調整")
print(f"{'='*60}")

root.destroy()
