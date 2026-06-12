import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pyaudio
import numpy as np
import jieba.analyse
import datetime
import os
import json
import warnings
import re

warnings.filterwarnings("ignore")

class UltimateWhisperCaptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra 即時字幕與關鍵字系統 (Faster-Whisper 核心防護版)")
        self.root.geometry("1000x650")
        self.root.configure(bg="#1E1E1E")
        
        self.is_listening = False
        self.lyrics_lines = []
        self.load_grammar()
        
        self.show_loading_window()
        threading.Thread(target=self.lazy_load_model, daemon=True).start()

    def show_loading_window(self):
        self.loading_label = tk.Label(
            self.root,
            text="正在初始化 Faster-Whisper AI 模型...\n(首次啟動會自動下載模型，請稍候)",
            font=("Microsoft JhengHei", 14),
            bg="#1E1E1E", fg="#FFFFFF"
        )
        self.loading_label.pack(expand=True)

    def load_grammar(self):
        if os.path.exists("lyrics_lines.json"):
            with open("lyrics_lines.json", "r", encoding="utf-8") as f:
                self.lyrics_lines = json.load(f)
            print(f"[Lyrics] 已載入 {len(self.lyrics_lines)} 句歌詞作為校正參考")

    def lazy_load_model(self):
        from faster_whisper import WhisperModel
        try:
            self.model = WhisperModel("small", device="cuda", compute_type="float16")
            print("[系統] 成功啟用 NVIDIA GPU (CUDA) 硬體加速！")
        except Exception as e:
            print(f"[系統] GPU 加速失敗 ({e})，自動切換至 CPU int8 模式...")
            self.model = WhisperModel("small", device="cpu", compute_type="int8")
            print("[系統] 已切換至 CPU 節能模式")
        self.root.after(0, self.transition_to_main_ui)

    def transition_to_main_ui(self):
        self.loading_label.destroy()
        self.setup_ui()
        self.setup_audio()

    def setup_ui(self):
        modern_font = ("Microsoft JhengHei", 12)
        title_font = ("Microsoft JhengHei", 12, "bold")
        
        control_frame = tk.Frame(self.root, bg="#1E1E1E")
        control_frame.pack(fill=tk.X, pady=10, padx=20)

        self.indicator = tk.Canvas(control_frame, width=20, height=20, bg="#1E1E1E", highlightthickness=0)
        self.indicator.pack(side=tk.LEFT, padx=(0, 10))
        self.indicator_light = self.indicator.create_oval(3, 3, 17, 17, fill="#555555")

        self.btn_start = tk.Button(control_frame, text="開始收音", font=modern_font, command=self.start_listening, bg="#4CAF50", fg="white", relief="flat", padx=10)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(control_frame, text="停止收音", font=modern_font, command=self.stop_listening, bg="#f44336", fg="white", state=tk.DISABLED, relief="flat", padx=10)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_export = tk.Button(control_frame, text="自選路徑匯出 TXT", font=modern_font, command=self.export_txt, bg="#2196F3", fg="white", relief="flat", padx=10)
        self.btn_export.pack(side=tk.RIGHT, padx=5)

        volume_frame = tk.Frame(self.root, bg="#1E1E1E")
        volume_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        tk.Label(volume_frame, text="麥克風音量：", font=modern_font, bg="#1E1E1E", fg="#E0E0E0").pack(side=tk.LEFT)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Horizontal.TProgressbar", thickness=15, troughcolor='#2D2D2D', background='#4CAF50')
        self.volume_bar = ttk.Progressbar(volume_frame, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.volume_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        content_frame = tk.Frame(self.root, bg="#1E1E1E")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        left_frame = tk.Frame(content_frame, bg="#1E1E1E")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        tk.Label(left_frame, text="左側：關鍵詞提取", font=title_font, bg="#1E1E1E", fg="#4CAF50").pack(anchor="w", pady=5)
        self.text_keywords = tk.Text(left_frame, font=("Microsoft JhengHei", 14), wrap=tk.WORD, bg="#2D2D2D", fg="#E0E0E0", insertbackground="white")
        self.text_keywords.pack(fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(content_frame, bg="#1E1E1E")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        tk.Label(right_frame, text="右側：通順語意句子 (支援手動校正)", font=title_font, bg="#1E1E1E", fg="#2196F3").pack(anchor="w", pady=5)
        self.text_sentences = tk.Text(right_frame, font=("Microsoft JhengHei", 14), wrap=tk.WORD, bg="#2D2D2D", fg="#FFFFFF", insertbackground="white")
        self.text_sentences.pack(fill=tk.BOTH, expand=True)

    def setup_audio(self):
        self.p = pyaudio.PyAudio()
        try:
            self.default_device_index = self.p.get_default_input_device_info()['index']
            self.stream = None
        except Exception:
            messagebox.showerror("錯誤", "找不到可用的麥克風設備！")
            self.root.destroy()

    def process_audio(self):
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2000)
        self.stream.start_stream()

        audio_buffer = bytearray()
        silence_chunks = 0

        while self.is_listening:
            try:
                data = self.stream.read(2000, exception_on_overflow=False)
                if len(data) == 0:
                    continue

                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                volume_level = min(100, int(rms / 25))
                self.root.after(0, self.update_volume_bar, volume_level)

                audio_buffer.extend(data)

                if rms < 160:
                    silence_chunks += 1
                else:
                    silence_chunks = 0

                if (silence_chunks >= 10 and len(audio_buffer) > 32000) or len(audio_buffer) >= 256000:
                    raw_audio = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_buffer = bytearray()
                    silence_chunks = 0

                    if len(raw_audio) > 8000:
                        # 雜訊閘：移除極低音量樣本，減少背景雜音干擾
                        gate_mask = np.abs(raw_audio) > 0.003
                        if np.any(gate_mask):
                            raw_audio = raw_audio * gate_mask.astype(np.float32)
                        # RMS 正規化：保持音量一致
                        rms_val = np.sqrt(np.mean(np.square(raw_audio)))
                        if rms_val > 0:
                            raw_audio = raw_audio / rms_val * 0.10

                        segments, info = self.model.transcribe(
                            raw_audio,
                            beam_size=10,
                            language="zh",
                            initial_prompt="大家好，今天我們要討論的主題是關於未來的發展方向。首先讓我們來看看目前的進度。",
                            temperature=0.0,
                            patience=2.0,
                            length_penalty=1.2,
                            repetition_penalty=1.1,
                            condition_on_previous_text=True,
                            vad_filter=True,
                            vad_parameters=dict(min_silence_duration_ms=500, threshold=0.3),
                            no_speech_threshold=0.7,
                            compression_ratio_threshold=2.0,
                            log_prob_threshold=-0.5,
                            suppress_blank=True
                        )

                        text = "".join([segment.text for segment in segments]).strip()
                        text = text.replace(" ", "")

                        if not text:
                            continue

                        if re.search(r'(.)\1{3,}', text):
                            print(f"【防護攔截重複幻覺】: {text}")
                            continue

                        corrected = self.match_lyrics(text)
                        keywords = jieba.analyse.extract_tags(corrected, topK=5, allowPOS=('n', 'vn', 'v'))
                        keyword_str = "、".join(keywords) if keywords else "..."
                        self.root.after(0, self.update_texts_and_obs, keyword_str, corrected)

            except Exception as e:
                print(f"【系統異常】: {e}")

        self.stream.stop_stream()
        self.stream.close()
        self.root.after(0, self.update_volume_bar, 0)

    def update_volume_bar(self, value):
        self.volume_bar['value'] = value

    def match_lyrics(self, text):
        if not self.lyrics_lines:
            return text
        best_match = text
        best_score = 0
        for line in self.lyrics_lines:
            common = sum(1 for c in text if c in line)
            score = common / max(len(text), len(line)) if text else 0
            if score > best_score:
                best_score = score
                best_match = line
        if best_score > 0.3:
            return best_match
        return text

    def update_texts_and_obs(self, keywords, sentence):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.text_keywords.insert(tk.END, f"[{timestamp}] {keywords}\n")
        self.text_keywords.see(tk.END)
        self.text_sentences.insert(tk.END, f"[{timestamp}] {sentence}\n")
        self.text_sentences.see(tk.END)
        try:
            with open("obs_subtitle.txt", "w", encoding="utf-8") as f:
                f.write(sentence)
        except Exception:
            pass

    def start_listening(self):
        self.is_listening = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.indicator.itemconfig(self.indicator_light, fill="#FF5252")
        threading.Thread(target=self.process_audio, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.indicator.itemconfig(self.indicator_light, fill="#555555")

    def export_txt(self):
        default_filename = f"會議紀錄_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="請選擇字幕紀錄儲存路徑"
        )
        if file_path:
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
                messagebox.showinfo("匯出成功", f"檔案已成功儲存至：\n{file_path}")
            except Exception as e:
                messagebox.showerror("匯出失敗", f"儲存檔案時發生錯誤:\n{str(e)}")

if __name__ == "__main__":
    jieba.initialize()
    root = tk.Tk()
    app = UltimateWhisperCaptionApp(root)
    root.mainloop()
