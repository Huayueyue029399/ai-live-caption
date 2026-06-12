"""過濾 grammar：只保留模型支援的詞彙，移除過長片語"""
import json
import os
import jieba

jieba.initialize()

with open("lyrics.txt", "r", encoding="utf-8") as f:
    lyrics = f.read()

words = set()

for line in lyrics.split("\n"):
    line = line.strip()
    if not line:
        continue
    segs = jieba.lcut(line)
    for w in segs:
        w = w.strip()
        if not w or w == " ":
            continue
        words.add(w)

# 常用中文字 (幾乎所有模型都支援)
common_chars = "我的了你是不在有就都也還又把被讓會能要很真好沒別可只才所以為但是如果因當從到給跟與對將她他連愛這長情人"
for c in common_chars:
    words.add(c)

# 只保留 1-4 字的短詞 (長片語模型不支援)
filtered = [w for w in sorted(words, key=lambda x: -len(x)) if len(w) <= 4]

print(f"原始詞彙: {len(words)}")
print(f"過濾後詞彙: {len(filtered)} (僅保留 <=4 字詞)")

with open("grammar.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False)

with open("lyrics_lines.json", "w", encoding="utf-8") as f:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    json.dump(lines, f, ensure_ascii=False)

print("grammar.json + lyrics_lines.json 已更新")
