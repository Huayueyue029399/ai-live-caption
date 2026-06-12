"""5 分鐘自動測試 + 比對歌詞準確度"""
import tkinter as tk
from tkinter import messagebox
import datetime
import os
import sys
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pro_caption_app as app_mod

with open("lyrics_lines.json", "r", encoding="utf-8") as f:
    lyrics_lines = json.load(f)

original_export = app_mod.UltimateWhisperCaptionApp.export_txt

results = {"total": 0, "matched": 0}

def auto_export(self):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"測試報告_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write(f" 匯出時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=========================================\n\n")
            f.write("【左側：關鍵詞紀錄】\n")
            f.write(self.text_keywords.get("1.0", tk.END).strip())
            f.write("\n\n" + "="*40 + "\n\n")
            f.write("【右側：通順語意紀錄 (包含人工現場校正)】\n")
            f.write(self.text_sentences.get("1.0", tk.END).strip())
        print(f"[自動儲存成功] {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        correct_count = 0
        total_count = 0
        for line in lyrics_lines:
            total_count += 1
            if line in content:
                correct_count += 1

        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        print(f"\n{'='*50}")
        print(f" 歌詞比對準確度報告")
        print(f"{'='*50}")
        print(f" 歌詞總行數: {total_count}")
        print(f" 正確匹配行數: {correct_count}")
        print(f" 準確度: {accuracy:.1f}%")
        print(f"{'='*50}")
        if accuracy >= 80:
            print(f" [OK] 已達目標 80%！")
        else:
            print(f" [..] 未達 80%，需繼續調整")

    except Exception as e:
        print(f"[自動儲存失敗] {e}")

app_mod.UltimateWhisperCaptionApp.export_txt = auto_export

root = tk.Tk()
app = app_mod.UltimateRealTimeCaptionApp(root)

def auto_stop_and_save():
    if app.is_listening:
        app.stop_listening()
    app.export_txt()
    print("[5分鐘測試完成]")

root.after(300000, auto_stop_and_save)

root.mainloop()
