"""驗證 grammar 詞彙覆蓋率與模擬辨識準確度"""
import jieba
import json
import sys

jieba.initialize()

with open("lyrics.txt", "r", encoding="utf-8") as f:
    lyrics = f.read()

with open("grammar.json", "r", encoding="utf-8") as f:
    grammar = json.load(f)

grammar_set = set(grammar)

lines = [l.strip() for l in lyrics.split("\n") if l.strip()]

total_chars = 0
matched_chars = 0
total_words = 0
matched_words = 0
error_details = []

for line in lines:
    segs = jieba.lcut(line)
    line_total = len([w for w in segs if w.strip() and w != " "])
    line_matched = 0
    line_errors = []
    for w in segs:
        w = w.strip()
        if not w or w == " ":
            continue
        total_chars += len(w)
        total_words += 1
        if w in grammar_set:
            matched_chars += len(w)
            matched_words += 1
            line_matched += 1
        else:
            line_errors.append(w)
    if line_errors:
        error_details.append((line, line_matched, line_total, line_errors))

word_accuracy = (matched_words / total_words * 100) if total_words > 0 else 0
char_accuracy = (matched_chars / total_chars * 100) if total_chars > 0 else 0

print(f"{'='*50}")
print(f" Grammar 詞彙覆蓋率驗證")
print(f"{'='*50}")
print(f" 詞彙總數 (grammar.json): {len(grammar)}")
print(f" 歌詞總詞數: {total_words}")
print(f" 覆蓋詞數: {matched_words}")
print(f" 詞級覆蓋率: {word_accuracy:.1f}%")
print(f" 字級覆蓋率: {char_accuracy:.1f}%")
print(f"{'='*50}")

if error_details:
    print(f"\n[!] 未覆蓋詞語 ({len(error_details)} 行有缺漏):")
    for line, matched, total, errors in error_details[:10]:
        print(f"  行: {line[:30]}...")
        print(f"  覆蓋: {matched}/{total} -> 缺少: {errors}")
else:
    print(f"\n[OK] 所有詞語均已覆蓋！")

target = 80.0
if word_accuracy >= target:
    print(f"\n[OK] 已達目標 {target}%！無需調整。")
else:
    print(f"\n[..] 未達目標 {target}% (目前 {word_accuracy:.1f}%)")
    print(f"   繼續擴充 grammar.json 中...")

print(f"{'='*50}")
