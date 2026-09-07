# 安裝：Cursor 與其他 agent

## Cursor

```bash
git clone https://github.com/Raymondhou0917/ai-level-check.git ~/ai-level-check
mkdir -p .cursor/rules
ln -s ~/ai-level-check/SKILL.md .cursor/rules/ai-level-check.mdc
```

或直接在對話裡：

```
讀 ~/ai-level-check/SKILL.md，照它的流程幫我跑 AI 使用檢核
```

**注意**：Cursor 自己的對話紀錄目前還沒有 collector 支援
（存在 `~/Library/Application Support/Cursor/` 的 SQLite 裡）。
所以在 Cursor 裡跑，分析的仍然是 `~/.claude/` 與 `~/.codex/` 的紀錄。

想補這塊的話，[references/log-sources.md](../references/log-sources.md#想加一個新來源)
有寫需要哪些欄位，歡迎 PR。

## 任何能讀 Markdown 的 agent

這個 skill 沒有用到任何平台專屬語法。最低限度是：

1. 讓它讀得到 `SKILL.md`
2. 讓它能執行 `python3 scripts/collect.py`
3. 讓它讀得到 `references/` 底下的檔案

第 2 點做不到的話，自己先在終端機跑一次 `collect.py`，
再把產出的 `metrics.md` 與 `cases.md` 貼給它。

## 完全沒有本機紀錄

例如只用 ChatGPT 網頁版、Gemini 網頁版。

那就走**貼上模式**：把 `SKILL.md` 貼給它，然後說

```
我沒有本機紀錄。請直接分析你在這個對話與專案裡讀得到的歷史，
並在報告開頭寫明分析範圍僅限於此。
```

這時候它會退回成「純 prompt」的用法——也就是這個專案最初的形態，
效果取決於那個平台讓它讀到多少東西。
