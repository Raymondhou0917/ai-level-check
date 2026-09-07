# CHANGELOG

本專案的版本紀錄。格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)。

## [0.1.0] - 2026-09-07

第一版。從有序設計陳敬儒的「有序 AI 工作力檢核 Prompt（通用版）」出發，
把單次貼上的 prompt 改造成可重複執行、有原始證據、可長期累積的開源 skill。

### 新增

- **`scripts/collect.py`**：掃 `~/.claude/projects/` 與 `~/.codex/sessions/`，
  產出證據包（`summary.json`／`metrics.md`／`cases.md`）。
  純標準庫，不連網、不上傳，預設去識別化。
- **human / automation / subagent 三向分流**：這是原版 prompt 沒有處理、
  但會決定整份報告成敗的一件事。同一個紀錄目錄裡同時躺著本人打的字，
  和本人寫的 bot 自己跑出來的 system prompt。同一批 14 天紀錄實測：不分流時
  對話 1255 則、「使用者發言長度中位數」16536 字、「交辦時給了條件」訊號 1214 次；
  分流後只算 human 是 42 則、120 字、17 次——所有行為訊號都會跟著失真。
  提問行為只算 human；automation 獨立列為 LV4–LV5 的實作證據。
- **`references/levels.md`**：LV0–LV5 量表，加上「證據包欄位 → 能支持什麼／
  明確不能支持什麼」的對照表。
- **`references/evidence-rules.md`**：證據歸屬六類、公平判斷八條、
  四種判定量表、七項核心能力、交付檢查。
- **`references/personas.md`**：16 型 AI 使用人物志（四軸：交辦／查核／沉澱／動手）。
  原版沒有這一層；加進來是為了讓報告有一個可以公開、可以聊的部分，
  同時把「等級」留在只給本人看的地方。
- **`references/privacy.md`**：三條紅線、資料處理、給公司與給個人的兩套用法。
- **`references/log-sources.md`**：Claude Code 與 Codex 紀錄格式的實測文件，
  含欄位分布數字。
- **`references/report-design.md`**：兩層報告結構與單檔 HTML 規範。
- **`scripts/publish.sh`**：推報告進團隊 private repo。
  不 force push、不覆蓋既有期間、不推 evidence、沒有 `--yes` 一定停下來確認、
  推之前掃一次金鑰。
- 安裝說明：Claude Code、Codex、Cursor、團隊部署。

### 與原版 prompt 的主要差異

| | 有序原版 | 本專案 |
| :-- | :-- | :-- |
| 證據來源 | AI 當下讀得到什麼就用什麼 | 掃本機紀錄，產出可核對的證據包 |
| 可重複性 | 每次貼上、結果隨平台浮動 | 同一份證據包可重跑、可比對 |
| 人機分流 | 未處理 | 三向分流，提問行為只算 human |
| 累積 | 單次報告 | 週期執行 ＋ git 存證 |
| 分型 | 無 | 16 型人物志 |
| 隱私 | 靠 prompt 內的規則 | 收集階段就去識別化，加上部署層的制度規範 |

原版已經處理好、本專案原樣保留的部分：證據歸屬、公平判斷、
四種判定量表、系統驗證四項、報告用語規則、禁止排名與百分位。
這些是原版最扎實的地方，沒有改的必要。
