# 安裝：Codex

## 安裝

```bash
git clone https://github.com/Raymondhou0917/ai-level-check.git ~/ai-level-check
ln -s ~/ai-level-check ~/.codex/skills/ai-level-check
```

Codex 版本較舊、沒有 `~/.codex/skills/` 時，把 `SKILL.md` 的內容
接在你的 `AGENTS.md` 後面，或在對話裡直接貼路徑請它讀。

## 用法

```
讀 ~/ai-level-check/SKILL.md，幫我跑這兩週的 AI 使用檢核
```

Codex 會照 SKILL.md 的流程走：先問同意閘門，再跑 `collect.py`，
然後讀 `references/` 產報告。

## 只要數字

```bash
python3 ~/ai-level-check/scripts/collect.py --days 14 --source codex
```

## 注意：Codex 的自動化紀錄特別多

`codex exec` 跑出來的對話會全部落在 `~/.codex/sessions/`。
在一台常跑自動化的機器上，這類紀錄可能佔九成以上。

`collect.py` 會依 `originator` 與 `thread_source` 自動分流，
把它們歸到 `automation` 而不是 `human`。跑完先看「對話分流」那一段，
確認 human 的數量合理，再往下看。

分流規則見 [references/log-sources.md](../references/log-sources.md#codex)。
