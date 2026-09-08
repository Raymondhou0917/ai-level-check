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

那就走**貼上模式**：打開 [`prompts/chat-paste.md`](../prompts/chat-paste.md)，複製那份 Prompt。
不要貼整份 `SKILL.md` 當網頁 Prompt，也不要說「照 Demo 再做一份」——Demo 是假資料，模型會直接抄走。
