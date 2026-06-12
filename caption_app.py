import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import speech_recognition as sr
import pyaudio
import numpy as np
import jieba.analyse
import datetime

class RealTimeCaptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("即時關鍵字與字幕系統")
        self.root.geometry("800x500")
        
        self.is_listening = False
        self.recognizer = sr.Recognizer()
        
        # 條件 4：提高麥克風敏感度 (降低門檻值，並開啟動態適應)
        self.recognizer.energy_threshold = 150  
        self.recognizer.dynamic_energy_threshold = True 
        
        self.setup_ui()
        self.setup_audio()

    def setup_ui(self):
        # 頂部控制區
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, pady=10, padx=10)

        self.btn_start = tk.Button(control_frame, text="開始收音", command=self.start_listening, bg="#4CAF50", fg="white")
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(control_frame, text="停止收音", command=self.stop_listening, bg="#f44336", fg="white", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # 條件 7：匯出成 TXT 按鈕
        self.btn_export = tk.Button(control_frame, text="匯出成 TXT", command=self.export_txt, bg="#2196F3", fg="white")
        self.btn_export.pack(side=tk.RIGHT, padx=5)

        # 條件 3：麥克風收音音量條
        volume_frame = tk.Frame(self.root)
        volume_frame.pack(fill=tk.X, padx=10)
        tk.Label(volume_frame, text="麥克風音量:").pack(side=tk.LEFT)
        self.volume_bar = ttk.Progressbar(volume_frame, orient="horizontal", length=300, mode="determinate")
        self.volume_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # 顯示區域 (左右分割)
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 條件 1：左半邊 - 聲音中的關鍵字
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(left_frame, text="關鍵字提取 (精華重點)", font=("Arial", 12, "bold")).pack()
        self.text_keywords = tk.Text(left_frame, font=("Arial", 14), wrap=tk.WORD)
        self.text_keywords.pack(fill=tk.BOTH, expand=True)

        # 條件 2：右半邊 - 通順語意句子
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        tk.Label(right_frame, text="即時通順語句 (完整語意)", font=("Arial", 12, "bold")).pack()
        self.text_sentences = tk.Text(right_frame, font=("Arial", 14), wrap=tk.WORD)
        self.text_sentences.pack(fill=tk.BOTH, expand=True)

    def setup_audio(self):
        # 條件 5：自動搜尋可用麥克風音源且自動使用
        self.p = pyaudio.PyAudio()
        try:
            default_device_index = self.p.get_default_input_device_info()['index']
            self.mic = sr.Microphone(device_index=default_device_index)
            print(f"已自動選用預設麥克風 (ID: {default_device_index})")
        except Exception as e:
            messagebox.showerror("錯誤", "找不到可用的麥克風設備！")
            self.root.destroy()

    def update_volume_meter(self):
        """更新音量條的背景執行緒"""
        stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        while self.is_listening:
            try:
                data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
                # 計算音量 RMS 值並映射到 0-100 的進度條
                rms = np.sqrt(np.mean(np.square(data)))
                volume = min(100, int(rms / 50)) 
                self.volume_bar['value'] = volume
            except:
                pass
        stream.stop_stream()
        stream.close()
        self.volume_bar['value'] = 0

    def process_audio(self):
        """處理語音辨識的背景執行緒"""
        with self.mic as source:
            # 依據環境噪音自動校準
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening:
                try:
                    # 進行收音
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    # 使用 Google 免費 API 進行中文語音辨識
                    sentence = self.recognizer.recognize_google(audio, language='zh-TW')
                    
                    if sentence:
                        # 條件 6：關鍵詞精度高 (使用 jieba TF-IDF 演算法提取名詞與動詞重點)
                        keywords = jieba.analyse.extract_tags(sentence, topK=3, allowPOS=('n', 'vn', 'v'))
                        keyword_str = "、".join(keywords) if keywords else "..."

                        # 更新 UI
                        self.root.after(0, self.update_texts, keyword_str, sentence)

                except sr.WaitTimeoutError:
                    continue # 沒聽到聲音，繼續監聽
                except sr.UnknownValueError:
                    continue # 聽不懂聲音，繼續監聽
                except Exception as e:
                    print(f"辨識發生錯誤: {e}")

    def update_texts(self, keywords, sentence):
        """安全地更新 Tkinter 介面"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 插入關鍵字到左邊
        self.text_keywords.insert(tk.END, f"[{timestamp}] {keywords}\n")
        self.text_keywords.see(tk.END)
        
        # 插入完整句子到右邊
        self.text_sentences.insert(tk.END, f"[{timestamp}] {sentence}\n")
        self.text_sentences.see(tk.END)

    def start_listening(self):
        self.is_listening = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        # 啟動音量條執行緒
        threading.Thread(target=self.update_volume_meter, daemon=True).start()
        # 啟動語音辨識執行緒
        threading.Thread(target=self.process_audio, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def export_txt(self):
        # 條件 7：將關鍵字與語句匯出成 TXT (儲存到桌面)
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = os.path.join(desktop, f"Caption_Record_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== 關鍵字紀錄 ===\n")
                f.write(self.text_keywords.get("1.0", tk.END))
                f.write("\n=== 完整語意紀錄 ===\n")
                f.write(self.text_sentences.get("1.0", tk.END))
            messagebox.showinfo("匯出成功", f"紀錄已成功儲存為：\n{filename}")
        except Exception as e:
            messagebox.showerror("匯出失敗", str(e))

if __name__ == "__main__":
    # 初始化結巴分詞
    jieba.initialize()
    
    root = tk.Tk()
    app = RealTimeCaptionApp(root)
    root.mainloop()
