# 紀錄從哪裡來

以下路徑與欄位都是在 macOS 上實際掃過驗證的（2026-09）。
各家版本會變，跑出來的數字不對勁時，先回來確認欄位還在不在。

---

## 支援狀況

| 工具 | 紀錄位置 | 狀態 |
| :-- | :-- | :-- |
| Claude Code（含 Desktop、CLI、Agent SDK） | `~/.claude/projects/<專案>/<session>.jsonl` | ✅ 已支援 |
| Codex（Desktop、CLI、exec） | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | ✅ 已支援 |
| Codex 封存 | `~/.codex/archived_sessions/…` | ✅ 已支援 |
| Cursor | `~/Library/Application Support/Cursor/`（SQLite） | ⬜ 未支援，歡迎 PR |
| Gemini CLI / Antigravity | `~/.gemini/`、`~/.antigravity/` | ⬜ 未支援，歡迎 PR |
| ChatGPT 網頁版 | 無本機紀錄 | ❌ 只能走匯出檔或貼上模式 |
| 公司內部 AI 工具 | 依實作 | ❌ 各自實作 collector |

**掃不到的來源要在報告開頭明講。** 只掃到 Codex 就說只掃到 Codex，
不要讓讀者以為這是這個人的全部。

---

## Claude Code

每一則對話一個 `.jsonl`，一行一筆事件。

### 關鍵欄位

| 欄位 | 用途 |
| :-- | :-- |
| `type` | `user` / `assistant` / `system` / `attachment` / `queue-operation` … 只有前兩種要看 |
| `timestamp` | ISO 8601，用來切期間 |
| `cwd` | 專案目錄，用來標案例名稱 |
| `entrypoint` | **最關鍵的一個欄位**，見下 |
| `origin.kind` | 值為 `human` 時代表這則是真人打的字 |
| `isSidechain` | `true` 代表這是子代理（subagent）的對話 |
| `message.model` | 用了哪個模型 |
| `message.content` | 字串，或 `[{type: text|thinking|tool_use|tool_result|image}]` |

### `entrypoint`：分辨人跟機器

實測一台機器上 1519 個檔案的分布：

| entrypoint | 檔案數 | 其中有 `origin.kind: human` |
| :-- | --: | --: |
| `sdk-cli` | 1438 | 0 |
| `claude-desktop` | 80 | 71 |
| `cli` | 1 | 0 |

`sdk-cli` 是透過 Agent SDK 跑的——排程、bot、CI。
那些對話裡的「user message」是**程式寫的 system prompt**，不是人打的字。

不分流會發生什麼：同一批 14 天的紀錄（Claude Code ＋ Codex），
混在一起算是 1255 則對話、發言長度中位數 16536 字、「交辦時給了條件」訊號 1214 次；
只算 human 是 42 則、120 字、17 次。

前者是 bot 的 system prompt，後者才是這個人打字的樣子。
所有行為訊號都會跟著一起壞掉。

所以 `collect.py` 的分類規則是：

```
isSidechain          → subagent
origin.kind == human → human
entrypoint 含 sdk / headless / print / action → automation
其餘                  → human
```

### 一則 user 訊息裡不只有人打的字

Claude Code 會把 `<system-reminder>`、hook 輸出、CLAUDE.md 注入，
當成**同一則 user 訊息裡的其他 text block** 送出去。

所以必須**逐 block 過濾**，不能把 content 陣列整包接起來當使用者說的話。
`collect.py` 的 `clean_user_text()` 就在做這件事。

---

## Codex

紀錄依日期分層：`~/.codex/sessions/YYYY/MM/DD/rollout-<時間>-<uuid>.jsonl`。

### 關鍵欄位

| 欄位 | 用途 |
| :-- | :-- |
| `type` | `session_meta` / `turn_context` / `event_msg` / `response_item` |
| `payload.type`（在 `response_item` 底下） | `message` / `reasoning` / `function_call` / `function_call_output` / `custom_tool_call` / `image_generation_call` |
| `payload.role` | `user` / `assistant` / `developer`，`developer` 是系統注入 |
| `payload.name` | 工具名：`exec_command`、`exec`、`view_image`、`update_plan`… |
| `payload.arguments` | JSON 字串，`cmd` 裡是實際指令 |

### `session_meta` 裡的分流依據

實測分布：

| 欄位 | 值 | 數量 |
| :-- | :-- | --: |
| `originator` | `codex_exec` | 2797 |
| | `Codex Desktop` | 223 |
| | `codex_work_desktop` | 44 |
| | `codex_sdk_ts` | 21 |
| `thread_source` | `null` | 2781 |
| | `user` | 222 |
| | `subagent` | 95 |

分類規則：

```
thread_source == subagent，或 source 含 subagent → subagent
thread_source == user                            → human
originator ∈ {Codex Desktop, codex_work_desktop, codex_cli_rs, codex-tui, …} → human
originator 含 exec / sdk，或 source == exec       → automation
```

### 寫檔怎麼抓

Codex 不用 Write／Edit 工具，走 `apply_patch`，檔名寫在指令內容裡：

```
*** Add File: path/to/file.md
*** Update File: path/to/other.py
```

注意 `arguments` 解出來的字串裡，換行可能還是字面上的 `\n`，
用 `\S+` 抓檔名會把後面的 diff 一起吃進去。要排除反斜線。

---

## 沒有本機紀錄的時候

兩條路：

1. **匯出檔**：ChatGPT、Claude 網頁版都可以匯出對話。
   匯出後請使用者指定檔案路徑，直接讀那份 JSON。
2. **貼上模式**：請使用者把最近的對話貼進來，
   或直接分析當前這個平台讀得到的歷史。

兩種都要在報告開頭寫明「本次未讀到本機紀錄，分析範圍僅限使用者提供的內容」。

---

## 想加一個新來源

寫一個 loader 回傳 `Session` 物件就好，需要填的欄位：

| 欄位 | 說明 |
| :-- | :-- |
| `kind` | `human` / `automation` / `subagent`，**這一欄最重要，判斷不出來就標 human 並在報告說明** |
| `driver` | 平台原始標記，方便追溯 |
| `started` / `ended` | 有時區的 datetime |
| `cwd` | 專案目錄或工作脈絡 |
| `user_msgs` | `[(timestamp, 真人打的字)]`，必須先過 `clean_user_text()` |
| `tools` | `Counter(工具名 → 次數)` |
| `bash_cmds` | 實際執行的指令字串 |
| `files_written` / `durable_writes` | 用 `note_write()` 加，會自動判斷是不是可複用位置 |

送 PR 時請附上：欄位分布的實測數字（像上面那兩張表），
以及分流規則為什麼這樣寫。沒有實測數字的 loader 不會合併——
猜出來的欄位會讓所有下游判斷一起錯。
