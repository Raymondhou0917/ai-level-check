#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-level-check / collect.py

把本機各家 AI coding agent 的對話紀錄，掃成一份「證據包」（evidence pack）。
只用 Python 3 標準庫，不裝套件、不連網、不上傳。

    python3 scripts/collect.py --days 14
    python3 scripts/collect.py --since 2026-08-01 --until 2026-08-31 --out evidence/2026-08
    python3 scripts/collect.py --days 30 --no-content     # 只出計數，不出任何原文
    python3 scripts/collect.py --days 14 --source codex
    python3 scripts/collect.py --days 14 --source antigravity

有裝 Claude Code、Codex、Antigravity 就掃；沒裝的來源自動略過。

產出：
    summary.json   可核對的發生次數（機器讀）
    metrics.md     同一份計數的人類可讀版
    cases.md       抽樣案例：使用者原句、工具序列、修正輪次、產出檔案

三條設計原則，對應 references/evidence-rules.md：

1. 這裡算得出來的只有「發生過幾次」，不是「做得好不好」。好不好由分析階段
   讀案例原文判斷。

2. 人打的字和機器打的字必須分開。同一個 ~/.claude/projects/ 目錄底下，
   同時躺著本人在終端機打的字，和本人寫的 bot 半夜自己跑出來的 system prompt。
   混在一起算，「平均提示詞長度」會變成兩萬字，所有行為訊號一起失真。
   所以每則對話先分類成 human / automation / subagent：
     - 提問行為只看 human，這才是「這個人怎麼下指令」。
     - automation 不是雜訊，是「這個人做出了不用他在場也會跑的東西」，
       獨立列成 LV4–LV5 的實作證據。

3. 預設去識別化：家目錄、Email、電話、常見金鑰格式在寫檔前就遮掉。
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter

HOME = os.path.expanduser("~")

# ---------------------------------------------------------------- 去識別化

REDACT_RULES = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{30,}"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"), "[REDACTED_JWT]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    (re.compile(r"\b(?:\+?886[\-\s]?|0)9\d{2}[\-\s]?\d{3}[\-\s]?\d{3}\b"), "[PHONE]"),
]


def redact(text):
    if not text:
        return ""
    text = text.replace(HOME, "~")
    for pat, rep in REDACT_RULES:
        text = pat.sub(rep, text)
    return text


def excerpt(text, limit=280):
    text = re.sub(r"\s+", " ", redact(text or "").strip())
    return text if len(text) <= limit else text[:limit] + "…"


# ---------------------------------------------------------------- 雜訊過濾

# 這些是系統注入、hook 輸出、指令回聲、逐字稿回灌，不是人打的字。
NOISE_PREFIX = (
    "<system-reminder", "<command-name", "<command-message", "<local-command",
    "<user-prompt-submit-hook", "<session-start-hook", "<ci-monitor-event",
    # Claude Code Monitor 看門事件以 user 身分寫進 transcript，
    # 開頭是裸的 <task-notification>，沒有被 <system-reminder> 包住。
    "<task-notification",
    "[SYSTEM NOTIFICATION - NOT USER INPUT]",
    "Caveat:", "[Request interrupted", "[No response requested]", "API Error",
    "<bash-input>", "<bash-stdout>", "<bash-stderr>", ">>> TRANSCRIPT",
    # Codex 會把可安裝的 plugin 清單塞進 user message；
    # Claude Code 的 Stop hook 條件也是以 user 身分注入的。兩者都不是人打的字。
    "<recommended_plugins", "<plugins>", "A session-scoped Stop hook",
)
NOISE_CONTAINS = (
    "# CLAUDE.md", "# AGENTS.md instructions", "<INSTRUCTIONS>",
    "<user_instructions>", "<environment_context>", "<permissions instructions>",
    "Codebase and user instructions are shown below",
    "Here is a list of plugins that are available but not installed",
)
# 把逐字稿回灌自己的行濾掉：「[30] assistant: …」「[6] tool exec call: …」
TRANSCRIPT_ECHO = re.compile(r"^\[\d+\]\s+(assistant|user|tool\b|system)")
# 有些 agent 把真正的需求包在固定標頭後，只留標頭後那一段
REQUEST_SPLIT = re.compile(r"##\s*My request:\s*", re.I)


def clean_user_text(text):
    """回傳真人實際打的內容；判定為系統注入或回灌時回傳空字串。"""
    if not text or not text.strip():
        return ""
    t = text.strip()
    if t.startswith(NOISE_PREFIX) or TRANSCRIPT_ECHO.match(t):
        return ""
    parts = REQUEST_SPLIT.split(t)
    if len(parts) > 1:
        t = parts[-1].strip()
    if any(k in t[:2000] for k in NOISE_CONTAINS):
        return ""
    return t


# ---------------------------------------------------------------- 訊號字典
# 只回答「這個行為出現過幾次」，不回答「做得對不對」。

CORRECTION_HINTS = [
    "不對", "錯了", "不是這樣", "重來", "再試一次", "你搞錯", "不要這樣", "改回",
    "不是我要的", "會壞", "失敗了", "還是不行", "跑不起來", "報錯", "又錯", "漏了",
    "wrong", "incorrect", "that's not", "try again", "revert", "undo", "still fail",
]
SPEC_HINTS = [
    "驗收", "完成標準", "規格", "限制是", "不要做", "先不要", "範圍是", "目標是",
    "背景是", "前提", "輸出格式", "請只", "務必", "不能改", "邊界",
    "acceptance", "requirement", "constraint", "do not", "must not", "scope",
]
VERIFY_HINTS = [
    "驗證", "查證", "確認一下", "跑測試", "測一下", "來源", "出處", "核對",
    "有沒有真的", "證據", "verify", "double check", "run the test", "source",
]
DELEGATE_HINTS = ["subagent", "平行", "併行", "分工", "交給", "delegate", "fan-out"]

VERIFY_CMD_PAT = re.compile(
    r"\b(pytest|npm (run )?test|yarn test|go test|cargo test|jest|vitest|"
    r"git diff|git status|git log|ruff|eslint|tsc|mypy|lint|shellcheck|make test)\b"
)
DURABLE_PATH_PAT = re.compile(
    r"(SKILL\.md|AGENTS\.md|CLAUDE\.md|\.cursorrules|/skills/|/workflows/|/scripts/|"
    r"\.github/workflows/|settings\.json|/hooks/|crontab|launchd|\.plist|Dockerfile|Makefile)"
)
ARTIFACT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
# 各家的委派工具名字都不一樣。只認 Claude Code 那組的話，
# 在 Codex 上會誤報成「沒有分工」，但紀錄裡明明有 spawn_agent。
DELEGATE_TOOLS = {
    "Agent", "Task", "SendMessage",                                  # Claude Code
    "spawn_agent", "wait_agent", "list_agents", "followup_task",     # Codex
}

HUMAN, AUTOMATION, SUBAGENT = "human", "automation", "subagent"

# Antigravity 對話庫裡，step_type=15 出現的工具名（2026-09 本機實測）。
# 排除 media_* / call_* 這種一次一號的雜訊。
AGY_TOOLS = {
    "run_command", "view_file", "replace_file_content", "grep_search",
    "find_by_name", "write_to_file", "call_mcp_tool", "list_dir",
    "manage_task", "search_web", "task_notification", "read_resource",
    "browser_subagent", "generate_image",
}

EFFORT_NOTE = (
    "最好的 AI 工作者是用最少的訊息數跟最少的 token 達到一樣的成果；"
    "但因為每個人對工作成果好的標準不同，這個數字無法直接拿來評估，僅供參考。"
    "訊息少有時代表 skill、harness 寫得夠完整，有時只是這段期間用得少。"
)

# ---------------------------------------------------------------- 自動化齒輪
#
# 「有沒有讓 AI 自己動起來」是 LV4–LV5 的核心，但講「自動化」太籠統。
# 這裡用五種驅動機制當共同語言，因為現代系統要讓一件事自己發生，
# 底層就只有這五種扳機。五種都會在硬碟上留痕跡：改了什麼檔、跑了什麼指令、
# 用了什麼工具，所以不需要另外蒐集資料，掃現有證據包就夠。
#
# 覆蓋度不是分數。沒有那個需求就不該用那顆齒輪，五顆全用過不比兩顆「好」。
# 詳見 references/automation-gears.md。

# 偵測必須分清楚「提到」與「做了」。`grep -n webhook` 只是在找字，
# 不是在架 webhook；`cat > x.py <<EOF` 的 heredoc 內文更會整段誤中。
# 所以每顆齒輪拆成三種各自獨立、都要求是「動作」的訊號：
#   path — 寫出了讓它發生的那個檔（最強）
#   cmd  — 跑了會改變系統狀態的動詞（不是查詢動詞）
#   tool — 用了只能用來建這件事的工具
GEAR_FIELDS = ("key", "name", "what", "path", "cmd", "tool")
AUTOMATION_GEARS = [
    dict(zip(GEAR_FIELDS, (
        "schedule", "① 時間排程", "時間到就動：Cron、launchd、排程任務",
        re.compile(r"((LaunchAgents|LaunchDaemons)/.*\.plist$|/crontab|\.cron(tab)?$)", re.I),
        re.compile(r"\b(crontab\s+-[el]|launchctl\s+(load|bootstrap|enable|kickstart)|"
                   r"schtasks\s+/create|systemctl\s+enable\s+\S+\.timer)\b", re.I),
        re.compile(r"^(CronCreate|CronDelete|ScheduleWakeup|"
                   r"mcp__scheduled-tasks__(create|update)_scheduled_task)$"),
    ))),
    dict(zip(GEAR_FIELDS, (
        "webhook", "② 網路鉤子", "外部事件推過來：Webhook、n8n、表單與金流回呼",
        re.compile(r"(webhook|/api/hooks?/|callback[-_]url)", re.I),
        re.compile(r"\b(ngrok\s+http|n8n\s+(start|import)|cloudflared\s+tunnel)\b", re.I),
        re.compile(r"^mcp__n8n"),
    ))),
    dict(zip(GEAR_FIELDS, (
        "lifecycle", "③ 生命週期鉤子", "進出關卡時攔一下：SessionStart、pre-commit、pre-push",
        re.compile(r"(\.claude/settings[^/]*\.json$|\.git/hooks/|/hooks/[^/]+\.(sh|py|js|ts)$|"
                   r"(pre-commit|pre-push|commit-msg)(\.\w+)?$|\.pre-commit-config)", re.I),
        re.compile(r"\b(git config\s+(--\S+\s+)?core\.hooksPath|pre-commit\s+install|"
                   r"husky\s+(install|add))\b", re.I),
        None,
    ))),
    dict(zip(GEAR_FIELDS, (
        "cicd", "④ 持續整合部署", "推上去就自動測試打包上線：GitHub Actions、Zeabur、Vercel",
        re.compile(r"(\.github/workflows/.*\.ya?ml$|\.gitlab-ci\.ya?ml$|"
                   r"(^|/)Dockerfile$|(^|/)(zeabur|vercel|netlify)\.json$)", re.I),
        re.compile(r"\b(gh\s+workflow\s+(run|enable)|vercel\s+(--prod|deploy)|"
                   r"netlify\s+deploy|docker\s+(build|push)|fly\s+deploy)\b", re.I),
        re.compile(r"^mcp__zeabur__(deploy|create-service|get-build-logs|redeploy)"),
    ))),
    dict(zip(GEAR_FIELDS, (
        "watchdog", "⑤ 守護與心跳", "倒下自動拉起、定時回報還活著：pm2、KeepAlive、healthcheck",
        re.compile(r"(watchdog|heartbeat|health-?check|keep-?alive)", re.I),
        re.compile(r"\b(pm2\s+(start|restart|save|startup)|supervisorctl\s+(start|restart)|"
                   r"systemctl\s+restart)\b", re.I),
        re.compile(r"^(Monitor|mcp__firecrawl__firecrawl_monitor_(create|run))$"),
    ))),
]


def cmd_action(cmd):
    """只留下指令真正執行的那一段：砍掉 heredoc 內文與管線後面的長文字。

    `cat > foo.py <<'EOF' …整份程式碼…` 會讓後面的內容整段誤中關鍵字，
    所以在第一個 `<<` 切斷，只看前面那個動詞。
    """
    return (cmd or "").split("<<")[0][:240]


def scan_gears(sessions):
    """掃五種自動化齒輪的痕跡。只回答「有沒有做過」，不回答「做得好不好」。

    掃的三個面都是已經蒐集好的資料，不額外讀任何檔案。
    """
    found = {g["key"]: {"seen_in": set(), "evidence": []} for g in AUTOMATION_GEARS}

    for s in sessions:
        corpus = ([("寫檔", p, "path") for p in s.files_written]
                  + [("指令", cmd_action(c), "cmd") for c in s.bash_cmds]
                  + [("工具", t, "tool") for t in s.tools])
        for g in AUTOMATION_GEARS:
            slot = found[g["key"]]
            for label, text, field in corpus:
                pat = g[field]
                if not (pat and text and pat.search(text)):
                    continue
                slot["seen_in"].add(s.kind)
                if len(slot["evidence"]) < 5:
                    item = "%s：`%s`" % (label, excerpt(text, 120))
                    if item not in slot["evidence"]:
                        slot["evidence"].append(item)
                break   # 同一則對話同一顆齒輪只記一次

    out = {
        "_note": (
            "覆蓋度不是分數，也不排名。沒有那個需求就不該用那顆齒輪，"
            "五顆全用過不比兩顆好。某顆沒出現只代表本期間未觀察到，不代表不會。"
            "偵測只認「做了」的動作（寫出設定檔、跑了會改變系統狀態的指令、"
            "用了只能用來建這件事的工具），不認「提到」。判準見 references/automation-gears.md。"
        ),
        "observed": [], "not_observed": [], "detail": {},
    }
    for g in AUTOMATION_GEARS:
        slot = found[g["key"]]
        seen = sorted(slot["seen_in"])
        out["detail"][g["key"]] = {
            "name": g["name"], "what": g["what"],
            "seen_in": seen, "evidence": slot["evidence"],
        }
        (out["observed"] if seen else out["not_observed"]).append(g["key"])
    out["observed_count"] = len(out["observed"])
    return out


# ---------------------------------------------------------------- 資料結構


class Session(object):
    """一次對話。跨來源統一成同一個形狀。"""

    def __init__(self, sid, source, path):
        self.id = sid
        self.source = source
        self.path = path
        self.kind = HUMAN            # human / automation / subagent
        self.driver = ""             # 平台原始標記，寫進報告方便追溯
        self.started = None
        self.ended = None
        self.cwd = None
        self.models = Counter()
        self.user_msgs = []          # [(ts, text)]
        self.tools = Counter()
        self.tool_seq = []
        self.bash_cmds = []
        self.files_written = set()
        self.durable_writes = set()
        self.human_marked = 0        # 平台明確標成「人打的」的訊息數
        self.title = ""              # Antigravity 註解標題，沒有就空
        self.tokens_in = 0
        self.tokens_out = 0
        self.tokens_cache_read = 0
        self.tokens_available = False
        self._usage_ids = set()

    def touch(self, ts):
        if not ts:
            return
        if self.started is None or ts < self.started:
            self.started = ts
        if self.ended is None or ts > self.ended:
            self.ended = ts

    def note_write(self, path):
        # 從指令字串裡挖出來的檔名常黏到反引號、引號或 diff 內容，先清一次；
        # 清完不像路徑（沒有副檔名也沒有斜線）就丟掉，不要讓髒資料進報告。
        path = (path or "").strip().strip("`'\"").rstrip(",;:")
        if not path or len(path) > 300:
            return
        if "." not in os.path.basename(path) and "/" not in path:
            return
        self.files_written.add(path)
        if DURABLE_PATH_PAT.search(path):
            self.durable_writes.add(path)

    @property
    def turns(self):
        return len(self.user_msgs)


def parse_ts(raw):
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def add_usage(sess, usage):
    """把一筆 usage 加進 session。

    Claude 每一輪都會把整段 cache_read 再寫一次，加總會變成幾億。
    輸入只算新寫入（input + cache_creation），cache 命中另外記，不當成「用了多少 token」。
    """
    if not isinstance(usage, dict):
        return
    inn = (usage.get("input_tokens") or 0)
    inn += usage.get("cache_creation_input_tokens") or 0
    inn += usage.get("cache_write_input_tokens") or 0
    cache_hit = usage.get("cache_read_input_tokens") or 0
    cache_hit += usage.get("cached_input_tokens") or 0
    out = usage.get("output_tokens") or 0
    out += usage.get("reasoning_output_tokens") or 0
    if inn or out or cache_hit:
        sess.tokens_in += inn
        sess.tokens_out += out
        sess.tokens_cache_read += cache_hit
        sess.tokens_available = True


def proto_walk(blob, depth=0, max_depth=12):
    """從 protobuf 遞迴抽出 UTF-8 字串。Antigravity 對話本體是 nested protobuf。"""
    i = 0
    n = len(blob or b"")
    blob = blob or b""
    while i < n:
        key = 0
        shift = 0
        ok = True
        while i < n:
            b = blob[i]
            i += 1
            key |= (b & 0x7f) << shift
            if not (b & 0x80):
                break
            shift += 7
            if shift > 35:
                ok = False
                break
        if not ok:
            break
        wt = key & 7
        fn = key >> 3
        if wt == 2:
            ln = 0
            shift = 0
            while i < n:
                b = blob[i]
                i += 1
                ln |= (b & 0x7f) << shift
                if not (b & 0x80):
                    break
                shift += 7
                if shift > 35:
                    ln = -1
                    break
            if ln < 0 or i + ln > n:
                break
            chunk = blob[i:i + ln]
            i += ln
            try:
                s = chunk.decode("utf-8")
                if s and "\x00" not in s:
                    printable = sum(c.isprintable() or c in "\n\t\r" for c in s) / max(len(s), 1)
                    if printable > 0.85:
                        yield depth, fn, s
                        continue
            except Exception:
                pass
            if depth < max_depth:
                for item in proto_walk(chunk, depth + 1, max_depth):
                    yield item
        elif wt == 0:
            while i < n:
                b = blob[i]
                i += 1
                if not (b & 0x80):
                    break
        elif wt == 1:
            i += 8
        elif wt == 5:
            i += 4
        else:
            break


def proto_unix_ts(blob):
    """從 protobuf varint 裡找出像 Unix 時間的值。"""
    i = 0
    blob = blob or b""
    n = len(blob)
    found = []
    while i < n:
        v = 0
        shift = 0
        while i < n:
            b = blob[i]
            i += 1
            v |= (b & 0x7f) << shift
            if not (b & 0x80):
                break
            shift += 7
            if shift > 63:
                break
        if 1_700_000_000 <= v <= 2_000_000_000:
            found.append(v)
    return found


def iter_jsonl(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except OSError:
        return


# ---------------------------------------------------------------- Claude Code

# entrypoint 是最乾淨的分流依據：sdk-* 是程式驅動的，cli / *-desktop 是人在打字。
CC_AUTOMATION_ENTRY = ("sdk", "headless", "print", "action")


def classify_claude(entrypoint, sidechain, human_marked):
    if sidechain:
        return SUBAGENT
    ep = (entrypoint or "").lower()
    if human_marked:
        return HUMAN
    if any(k in ep for k in CC_AUTOMATION_ENTRY):
        return AUTOMATION
    return HUMAN


def load_claude_code(root, since, until):
    sessions = []
    for path in glob.glob(os.path.join(root, "projects", "*", "*.jsonl")):
        sid = os.path.splitext(os.path.basename(path))[0]
        sess = Session(sid, "claude-code", path)
        entrypoint, sidechain, hit = None, False, False
        for d in iter_jsonl(path):
            typ = d.get("type")
            if d.get("entrypoint") and not entrypoint:
                entrypoint = d["entrypoint"]
            if typ not in ("user", "assistant"):
                continue
            ts = parse_ts(d.get("timestamp"))
            if ts and not (since <= ts <= until):
                continue
            hit = True
            sess.touch(ts)
            sess.cwd = sess.cwd or d.get("cwd")
            if d.get("isSidechain"):
                sidechain = True
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            if typ == "assistant":
                if msg.get("model"):
                    sess.models[msg["model"]] += 1
                mid = msg.get("id")
                if mid and mid not in sess._usage_ids:
                    sess._usage_ids.add(mid)
                    add_usage(sess, msg.get("usage") or {})
            origin = d.get("origin") or {}
            marked = isinstance(origin, dict) and origin.get("kind") == "human"
            content = msg.get("content")
            if isinstance(content, str):
                if typ == "user":
                    cleaned = clean_user_text(content)
                    if cleaned:
                        sess.user_msgs.append((ts, cleaned))
                        sess.human_marked += 1 if marked else 0
                continue
            if not isinstance(content, list):
                continue
            # 一則 user 訊息常同時含真人輸入與系統附加的 <system-reminder>，
            # 必須逐 block 過濾，不能整包接起來當成使用者說的話。
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                bt = blk.get("type")
                if bt == "text" and typ == "user":
                    cleaned = clean_user_text(blk.get("text"))
                    if cleaned:
                        sess.user_msgs.append((ts, cleaned))
                        sess.human_marked += 1 if marked else 0
                elif bt == "tool_use":
                    name = blk.get("name") or "unknown"
                    sess.tools[name] += 1
                    sess.tool_seq.append(name)
                    inp = blk.get("input") or {}
                    if not isinstance(inp, dict):
                        continue
                    if name == "Bash" and isinstance(inp.get("command"), str):
                        sess.bash_cmds.append(inp["command"])
                    fp = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
                    if name in ARTIFACT_TOOLS and isinstance(fp, str):
                        sess.note_write(fp)
        if hit and (sess.user_msgs or sess.tools):
            sess.driver = entrypoint or "unknown"
            sess.kind = classify_claude(entrypoint, sidechain, sess.human_marked)
            sessions.append(sess)
    return sessions


# ---------------------------------------------------------------- Codex

CODEX_INJECT_PAT = re.compile(
    r"^\s*(#\s*AGENTS\.md|<INSTRUCTIONS>|<permissions instructions>|<environment_context>|"
    r"<user_instructions>|# Instructions|Distinguish instructions in attached documents)"
)
CODEX_HUMAN_ORIGINATORS = {
    "codex desktop", "codex_work_desktop", "codex_cli_rs", "codex-tui",
    "codex-chrome-extension-sidepanel", "vscode",
}


def classify_codex(meta):
    thread = (meta.get("thread_source") or "").lower()
    if thread == "subagent":
        return SUBAGENT
    src = meta.get("source")
    if isinstance(src, dict) and "subagent" in src:
        return SUBAGENT
    if thread == "user":
        return HUMAN
    orig = str(meta.get("originator") or "").lower()
    if orig in CODEX_HUMAN_ORIGINATORS:
        return HUMAN
    if "exec" in orig or "sdk" in orig or src == "exec":
        return AUTOMATION
    return HUMAN


def load_codex(root, since, until):
    sessions = []
    paths = (glob.glob(os.path.join(root, "sessions", "*", "*", "*", "*.jsonl"))
             + glob.glob(os.path.join(root, "archived_sessions", "*", "*", "*", "*.jsonl")))
    for path in paths:
        sid = os.path.splitext(os.path.basename(path))[0]
        sess = Session(sid, "codex", path)
        meta, hit = {}, False
        for d in iter_jsonl(path):
            typ = d.get("type")
            p = d.get("payload") or {}
            if typ == "session_meta":
                meta = p
                sess.cwd = sess.cwd or p.get("cwd")
                if p.get("model"):
                    sess.models[p["model"]] += 1
                continue
            ts = parse_ts(d.get("timestamp"))
            if ts and not (since <= ts <= until):
                continue
            if typ == "turn_context":
                sess.cwd = sess.cwd or p.get("cwd")
                if p.get("model"):
                    sess.models[p["model"]] += 1
                continue
            if typ == "event_msg":
                pt = (p.get("type") or "")
                if pt == "token_count":
                    info = p.get("info") or {}
                    total = info.get("total_token_usage") or {}
                    if total:
                        sess.tokens_in = (total.get("input_tokens") or 0) + (
                            total.get("cache_write_input_tokens") or 0)
                        sess.tokens_out = (
                            (total.get("output_tokens") or 0)
                            + (total.get("reasoning_output_tokens") or 0)
                        )
                        sess.tokens_cache_read = total.get("cached_input_tokens") or 0
                        sess.tokens_available = True
                continue
            if typ == "token_usage_record":
                continue
            if typ != "response_item":
                continue
            hit = True
            sess.touch(ts)
            pt = p.get("type")
            if pt == "message" and p.get("role") == "user":
                for c in p.get("content") or []:
                    if not (isinstance(c, dict) and c.get("type") in ("input_text", "text")):
                        continue
                    raw = c.get("text") or ""
                    if CODEX_INJECT_PAT.match(raw.strip()):
                        continue
                    cleaned = clean_user_text(raw)
                    if cleaned:
                        sess.user_msgs.append((ts, cleaned))
            elif pt in ("function_call", "custom_tool_call"):
                name = p.get("name") or "unknown"
                sess.tools[name] += 1
                sess.tool_seq.append(name)
                args = p.get("arguments") or p.get("input") or ""
                cmd = ""
                if isinstance(args, str):
                    try:
                        parsed = json.loads(args)
                        cmd = parsed.get("cmd") or parsed.get("command") or ""
                        if isinstance(cmd, list):
                            cmd = " ".join(str(x) for x in cmd)
                    except Exception:
                        cmd = args
                if cmd:
                    sess.bash_cmds.append(cmd)
                    # Codex 寫檔走 apply_patch，檔名在 *** Add File: / *** Update File: 後面。
                    # cmd 是 JSON 解出來的字串，裡面的換行可能還是字面上的 \n，
                    # 用 \S+ 會把後面的 diff 內容一起吃進檔名，所以排除反斜線。
                    for m in re.finditer(r"\*\*\* (?:Add|Update) File:\s*([^\s\\]+)", cmd):
                        sess.note_write(m.group(1))
                    for m in re.finditer(
                            r"(?:>|>>|tee)\s+(\S+\.(?:md|py|ts|tsx|js|json|ya?ml|sh|html|css))", cmd):
                        sess.note_write(m.group(1))
            elif pt == "image_generation_call":
                sess.tools["image_generation"] += 1
                sess.tool_seq.append("image_generation")
        if hit and (sess.user_msgs or sess.tools):
            sess.kind = classify_codex(meta)
            sess.driver = str(meta.get("originator") or "unknown")
            sessions.append(sess)
    return sessions


# ---------------------------------------------------------------- Antigravity
#
# 對話在 ~/.gemini/antigravity/conversations/<uuid>.db（桌面）
# 與 ~/.gemini/antigravity-cli/conversations/<uuid>.db（CLI）。
# 本體是 sqlite + nested protobuf。沒裝就整段跳過。
# 2026-09 實測：trajectory_meta.source 1＝桌面、17＝CLI；
# step_type 14＝本人發言，15＝模型／工具步驟。

AGY_USER_STEP = 14
AGY_TOOL_STEPS = {15, 8, 21, 5, 7, 9, 23, 101}
AGY_TITLE_RE = re.compile(r'title:"((?:\\.|[^"\\])*)"')


def agy_title(ann_path):
    if not os.path.isfile(ann_path):
        return ""
    try:
        text = open(ann_path, encoding="utf-8", errors="ignore").read(4000)
    except OSError:
        return ""
    m = AGY_TITLE_RE.search(text)
    if not m:
        return ""
    return m.group(1).replace('\\"', '"').strip()


def agy_user_text(payload):
    """type 14 裡 depth=1 field=2 是整段本人發言（本機實測）。"""
    best = ""
    for depth, fn, s in proto_walk(payload):
        s = (s or "").strip()
        if depth == 1 and fn == 2 and len(s) > len(best):
            best = s
    return best


def agy_tools_in(payload):
    names = set()
    for depth, fn, s in proto_walk(payload):
        t = (s or "").strip()
        if t in AGY_TOOLS:
            names.add(t)
        elif t.startswith("/") and "." in os.path.basename(t) and len(t) < 300:
            names.add("__path__:" + t)
    return names


def classify_agy(parent_rows):
    if parent_rows:
        return SUBAGENT
    return HUMAN


def load_one_agy_db(path, driver, since, until, title=""):
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=1)
    except sqlite3.Error:
        return None
    try:
        sid = os.path.splitext(os.path.basename(path))[0]
        sess = Session(sid, "antigravity", path)
        sess.driver = driver
        sess.title = title
        parent_n = 0
        try:
            parent_n = con.execute("SELECT COUNT(*) FROM parent_references").fetchone()[0]
        except sqlite3.Error:
            pass
        sess.kind = classify_agy(parent_n)
        hit = False
        try:
            rows = con.execute(
                "SELECT idx, step_type, metadata, step_payload FROM steps ORDER BY idx"
            ).fetchall()
        except sqlite3.Error:
            con.close()
            return None
        for idx, stype, meta, payload in rows:
            unix = proto_unix_ts(meta)
            ts = None
            if unix:
                try:
                    ts = dt.datetime.fromtimestamp(unix[0]).astimezone()
                except (OSError, OverflowError, ValueError):
                    ts = None
            if ts and not (since <= ts <= until):
                continue
            if ts:
                hit = True
                sess.touch(ts)
            if stype == AGY_USER_STEP:
                raw = agy_user_text(payload)
                cleaned = clean_user_text(raw) if raw else ""
                sess.user_msgs.append((ts, cleaned))
                sess.human_marked += 1
            elif stype in AGY_TOOL_STEPS:
                for name in agy_tools_in(payload):
                    if name.startswith("__path__:"):
                        sess.note_write(name.split(":", 1)[1])
                    else:
                        sess.tools[name] += 1
                        sess.tool_seq.append(name)
        try:
            for blob, in con.execute("SELECT data FROM gen_metadata"):
                for depth, fn, s in proto_walk(blob):
                    if fn == 19 and s.startswith("gemini"):
                        sess.models[s] += 1
                    elif s.startswith("file:///"):
                        path_s = s.replace("file://", "")
                        if not path_s.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4")):
                            sess.cwd = sess.cwd or path_s
        except sqlite3.Error:
            pass
        try:
            for blob, in con.execute("SELECT data FROM trajectory_metadata_blob"):
                for depth, fn, s in proto_walk(blob):
                    if s.startswith("file:///"):
                        path_s = s.replace("file://", "")
                        if not path_s.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4")):
                            sess.cwd = sess.cwd or path_s
                        break
        except sqlite3.Error:
            pass
        con.close()
        if not hit:
            # 步驟沒有可用時間戳時，退回檔案 mtime。
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
            if not (since <= mtime <= until):
                return None
            sess.touch(mtime)
        if sess.user_msgs or sess.tools:
            return sess
        return None
    except sqlite3.Error:
        try:
            con.close()
        except Exception:
            pass
        return None


def load_antigravity(since, until):
    """有裝 Antigravity 才掃；目錄不存在就回空清單。"""
    sessions = []
    roots = [
        (os.path.join(HOME, ".gemini", "antigravity", "conversations"),
         os.path.join(HOME, ".gemini", "antigravity", "annotations"),
         "antigravity"),
        (os.path.join(HOME, ".gemini", "antigravity-cli", "conversations"),
         os.path.join(HOME, ".gemini", "antigravity-cli", "annotations"),
         "antigravity-cli"),
    ]
    for conv_dir, ann_dir, driver in roots:
        if not os.path.isdir(conv_dir):
            continue
        for path in glob.glob(os.path.join(conv_dir, "*.db")):
            # 檔案在期間開始前就沒再動過，跳過。結束日之後還在改的，仍要打開看步驟時間。
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if mtime < since.timestamp():
                continue
            sid = os.path.splitext(os.path.basename(path))[0]
            title = agy_title(os.path.join(ann_dir, sid + ".pbtxt"))
            got = load_one_agy_db(path, driver, since, until, title)
            if got:
                sessions.append(got)
    return sessions


# ---------------------------------------------------------------- 統計


def count_hits(texts, hints):
    n = 0
    for t in texts:
        low = t.lower()
        if any(h.lower() in low for h in hints):
            n += 1
    return n


def agg(sessions):
    tools, bash, files, durable, days = Counter(), [], set(), set(), set()
    for s in sessions:
        tools.update(s.tools)
        bash.extend(s.bash_cmds)
        files |= s.files_written
        durable |= s.durable_writes
        if s.started:
            days.add(s.started.date().isoformat())
    return tools, bash, files, durable, days


def build_summary(sessions, since, until, sources):
    human = [s for s in sessions if s.kind == HUMAN]
    auto = [s for s in sessions if s.kind == AUTOMATION]
    sub = [s for s in sessions if s.kind == SUBAGENT]

    h_msgs = [t for s in human for _, t in s.user_msgs if t]
    h_msg_n = sum(len(s.user_msgs) for s in human)
    # 修正只能發生在第一次交辦之後。第一則就算含「錯了」，那是在說明問題，
    # 不是在修正 AI 這一輪的產出。案例抽樣用同一條規則，兩邊數字才對得起來。
    h_followups = [t for s in human for _, t in s.user_msgs[1:] if t]

    tok_human = [s for s in human if s.tokens_available]
    tok_in = sum(s.tokens_in for s in tok_human)
    tok_out = sum(s.tokens_out for s in tok_human)
    tok_cache = sum(s.tokens_cache_read for s in tok_human)
    tok_sources = sorted({s.source for s in tok_human})
    missing_tok = sorted({s.source for s in human} - set(tok_sources))
    h_tools, h_bash, h_files, h_durable, h_days = agg(human)
    a_tools, a_bash, a_files, a_durable, a_days = agg(auto)

    lens = sorted(len(t) for t in h_msgs) or [0]

    def pct(p):
        return lens[min(len(lens) - 1, int(len(lens) * p))]

    total_calls = sum(h_tools.values())
    mcp_calls = sum(v for k, v in h_tools.items() if k.startswith("mcp__"))

    return {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "period": {"since": since.date().isoformat(), "until": until.date().isoformat()},
        "sources": sources,
        "disclaimer": (
            "以下全部是可核對的發生次數，不是能力分數。提示詞長度、對話輪數、工具數量"
            "僅描述樣本，依 references/evidence-rules.md 不得作為能力高低的依據。"
        ),
        "session_split": {
            "_note": (
                "human＝本人在鍵盤前打的字；automation＝本人寫的程式或排程驅動的對話，"
                "不列入提問行為，改列為自動化實作證據；subagent＝被主對話派出去的子代理。"
            ),
            "human": len(human),
            "automation": len(auto),
            "subagent": len(sub),
            "drivers": dict(Counter(s.driver for s in sessions).most_common(10)),
        },
        "habitats": {
            "_note": (
                "本人操作落在幾個獨立入口。兩個來源都有對話，是 LV5 多棲的線索，"
                "不是分數；共用層有沒有接上、一家掛掉時切不切得過去，要看案例與規則入口。"
            ),
            "human_by_source": dict(Counter(s.source for s in human)),
            "human_source_count": len({s.source for s in human}),
            "automation_by_source": dict(Counter(s.source for s in auto)),
        },
        "human_usage": {
            "sessions": len(human),
            "sessions_with_tools": sum(1 for s in human if s.tools),
            "active_days": len(h_days),
            "user_messages": h_msg_n,
            "platform_marked_human": sum(s.human_marked for s in human),
            "projects": sorted({redact(s.cwd) for s in human if s.cwd})[:40],
            "models": dict(Counter(m for s in human for m in s.models.elements()).most_common(10)),
            "tool_calls": total_calls,
            "unique_tools": len(h_tools),
            "mcp_calls": mcp_calls,
            "mcp_ratio": round(mcp_calls / total_calls, 3) if total_calls else 0.0,
            "top_tools": dict(h_tools.most_common(25)),
        },
        "behaviour_signals": {
            "_note": ("訊號＝出現過的次數。出現不等於做得好，沒出現不等於不會，判斷交給分析階段讀案例原文。"
                      "correction_turns 只算每則對話第一次交辦之後的發言。"),
            "spec_turns": count_hits(h_msgs, SPEC_HINTS),
            "correction_turns": count_hits(h_followups, CORRECTION_HINTS),
            "verify_turns": count_hits(h_msgs, VERIFY_HINTS),
            "delegate_turns": count_hits(h_msgs, DELEGATE_HINTS),
            "verify_commands": sum(1 for c in h_bash if VERIFY_CMD_PAT.search(c)),
            "delegate_tool_calls": sum(v for k, v in h_tools.items() if k in DELEGATE_TOOLS),
            "multi_turn_sessions": sum(1 for s in human if s.turns >= 3),
        },
        "artifacts": {
            "files_written": len(h_files),
            "durable_write_count": len(h_durable),
            "durable_writes": sorted(redact(p) for p in h_durable)[:60],
        },
        "automation_evidence": {
            "_note": (
                "這一段不評估提問技巧，而是「本人不在場時，他做的東西還跑不跑」。"
                "有紀錄代表確實跑過；跑得對不對要看案例，不能只憑跑過就給 LV5。"
            ),
            "sessions": len(auto),
            "active_days": len(a_days),
            "tool_calls": sum(a_tools.values()),
            "distinct_entrypoints": sorted({s.driver for s in auto})[:10],
            "top_tools": dict(a_tools.most_common(10)),
            "files_written": len(a_files),
            "durable_writes": sorted(redact(p) for p in a_durable)[:20],
            "subagent_sessions": len(sub),
        },
        "automation_gears": scan_gears(sessions),
        "sample_description_only": {
            "_note": "只描述樣本長相，不評分。短提問不是弱點，長提問也不是能力。",
            "user_msg_len_p50": pct(0.5),
            "user_msg_len_p90": pct(0.9),
        },
        "effort": {
            "_note": EFFORT_NOTE,
            "human_sessions": len(human),
            "human_user_messages": h_msg_n,
            "messages_per_session": round(h_msg_n / len(human), 1) if human else 0,
            "tokens_input": tok_in,
            "tokens_output": tok_out,
            "tokens_total": tok_out,
            "tokens_cache_read": tok_cache,
            "tokens_from_sources": tok_sources,
            "tokens_unavailable_sources": missing_tok,
            "human_messages_by_source": dict(Counter(
                src for s in human for src in [s.source] for _ in s.user_msgs
            )),
        },
    }


# ---------------------------------------------------------------- 案例抽樣


def score_case(s):
    """挑「看得到完整事件」的對話：有需求、有動手、有修正、有產出。"""
    sc = min(s.turns, 8) + min(len(s.tools), 6)
    sc += 3 if s.tools else 0
    sc += 4 if s.files_written else 0
    sc += 5 if s.durable_writes else 0
    texts = [t for _, t in s.user_msgs]
    if count_hits(texts[1:], CORRECTION_HINTS):
        sc += 6
    if count_hits(texts, SPEC_HINTS):
        sc += 4
    return sc


def render_one_case(idx, s, with_content):
    out = []
    label = (s.title or "").strip() or os.path.basename(redact(s.cwd or "")) or "未標示專案"
    out.append("## 案例 %d：%s" % (idx, label))
    out.append("")
    out.append("- 類型：`%s`（驅動來源 `%s`）　來源：`%s`　對話 ID：`%s`"
               % (s.kind, redact(s.driver), s.source, s.id))
    out.append("- 期間：%s → %s" % (
        s.started.strftime("%Y-%m-%d %H:%M") if s.started else "?",
        s.ended.strftime("%Y-%m-%d %H:%M") if s.ended else "?"))
    out.append("- 使用者發言 %d 次｜工具呼叫 %d 次｜不同工具 %d 種"
               % (s.turns, sum(s.tools.values()), len(s.tools)))
    if s.tools:
        out.append("- 主要工具：" + "、".join("%s×%d" % (k, v) for k, v in s.tools.most_common(8)))
    if s.files_written:
        out.append("- 寫入檔案 %d 個：%s" % (
            len(s.files_written),
            "、".join("`%s`" % redact(p) for p in sorted(s.files_written)[:6])))
    if s.durable_writes:
        out.append("- 其中落在可複用位置：" + "、".join("`%s`" % redact(p) for p in sorted(s.durable_writes)[:6]))
    texts = [t for _, t in s.user_msgs]
    # 修正＝第一次交辦「之後」才發生的事。第一則本身不算修正，
    # 否則「這個連結放錯了，你檢查一下」會同時被當成交辦與修正。
    # automation 對話的「使用者發言」是程式寫的 system prompt，談不上修正。
    corr = ([t for t in texts[1:] if any(h.lower() in t.lower() for h in CORRECTION_HINTS)]
            if s.kind == HUMAN else [])
    if corr:
        out.append("- 出現修正發言 %d 次" % len(corr))
    out.append("")
    if with_content and texts:
        out.append("<details><summary>使用者原句摘錄（去識別化）</summary>")
        out.append("")
        out.append("**第一次交辦**")
        out.append("")
        out.append("> " + excerpt(texts[0], 400))
        out.append("")
        if corr:
            out.append("**修正時說了什麼**")
            out.append("")
            for cc in corr[:3]:
                out.append("> " + excerpt(cc, 300))
                out.append("")
        if len(texts) > 1:
            out.append("**最後一次發言**")
            out.append("")
            out.append("> " + excerpt(texts[-1], 300))
            out.append("")
        out.append("</details>")
        out.append("")
    return out


def render_cases(sessions, limit, with_content):
    human = sorted([s for s in sessions if s.kind == HUMAN], key=score_case, reverse=True)
    auto = sorted([s for s in sessions if s.kind == AUTOMATION], key=score_case, reverse=True)

    out = ["# 抽樣案例（給分析階段當原始證據）", ""]
    out.append("每則案例只呈現可核對的紀錄：使用者原句、工具序列、修正輪次、產出檔案。")
    out.append("報告要沿用這裡的案例編號，不要重新編號，也不要把同一次事件拆成多個發現。")
    out.append("")
    out.append("- `human` 案例回答「這個人怎麼交辦、怎麼修正、怎麼驗收」。")
    out.append("- `automation` 案例回答「他做出來的東西，在他不在場時跑成什麼樣」，")
    out.append("  是 LV4–LV5 的實作線索，**不能**拿來評斷他的提問技巧。")
    out.append("")

    idx = 0
    if human:
        out += ["---", "", "# 一、本人操作的案例", ""]
        for s in human[:limit]:
            idx += 1
            out += render_one_case(idx, s, with_content)
    if auto:
        out += ["---", "", "# 二、自動化執行的案例（本人不在場）", ""]
        for s in auto[:max(2, limit // 3)]:
            idx += 1
            out += render_one_case(idx, s, with_content)
    if not human and not auto:
        out.append("_這個期間沒有掃到可用的對話紀錄。分析階段請直接寫「無法定級」，"
                   "不要拿 LV0 當預設值。_")
    return "\n".join(out)


def render_metrics(s):
    L = ["# 證據包計數：%s → %s" % (s["period"]["since"], s["period"]["until"]), ""]
    L += ["> %s" % s["disclaimer"], ""]

    sp = s["session_split"]
    L += ["## 對話分流", "", "> %s" % sp["_note"], ""]
    L += ["| 類型 | 對話數 |", "| :-- | --: |"]
    L += ["| 本人操作 human | %d |" % sp["human"],
          "| 自動化執行 automation | %d |" % sp["automation"],
          "| 子代理 subagent | %d |" % sp["subagent"], ""]
    L += ["驅動來源：" + "、".join("`%s`×%d" % (k, v) for k, v in sp["drivers"].items()), ""]
    hab = s.get("habitats") or {}
    if hab:
        L += ["## 多棲（獨立入口）", "", "> %s" % hab.get("_note", ""), ""]
        L += ["本人操作出現在 **%d** 個來源。" % hab.get("human_source_count", 0), ""]
        L += ["| 來源 | 本人操作 | 自動化 |", "| :-- | --: | --: |"]
        keys = sorted(set(hab.get("human_by_source", {})) | set(hab.get("automation_by_source", {})))
        for k in keys:
            L.append("| `%s` | %d | %d |" % (
                k,
                hab.get("human_by_source", {}).get(k, 0),
                hab.get("automation_by_source", {}).get(k, 0)))
        L.append("")

    h = s["human_usage"]
    L += ["## 本人操作的範圍", "", "| 項目 | 數字 |", "| :-- | --: |"]
    L += ["| 對話數（session） | %d |" % h["sessions"],
          "| 本人打出去的訊息 | %d |" % h["user_messages"],
          "| 其中有實際動手（有工具呼叫） | %d |" % h["sessions_with_tools"],
          "| 有紀錄的天數 | %d |" % h["active_days"],
          "| 平台明確標成「人打的」 | %d |" % h["platform_marked_human"],
          "| 涵蓋專案 | %d |" % len(h["projects"]), ""]
    L += ["模型：" + ("、".join("%s×%d" % (k, v) for k, v in h["models"].items()) or "紀錄未標示"), ""]

    ef = s.get("effort") or {}
    if ef:
        L += ["## 工作量（僅供參考，不是分數）", "", "> %s" % ef.get("_note", EFFORT_NOTE), ""]
        L += ["| 項目 | 數字 | 讀法 |", "| :-- | --: | :-- |"]
        rows = [
            "| 本人開了幾則對話 | %d | 一次對話裡可能來回很多次 |" % ef.get("human_sessions", 0),
            "| 本人打出去幾則訊息 | %d | 真正按發送的次數 |" % ef.get("human_user_messages", 0),
            "| 平均一則對話幾則訊息 | %s | 低不一定比較好 |" % ef.get("messages_per_session", 0),
        ]
        by = ef.get("human_messages_by_source") or {}
        for k, v in by.items():
            rows.append("| 其中 `%s` 發言 | %d | 只描述樣本 |" % (k, v))
        tok = ef.get("tokens_output") or 0
        miss = "、".join("`%s`" % x for x in (ef.get("tokens_unavailable_sources") or [])) or "無"
        src = "、".join("`%s`" % x for x in (ef.get("tokens_from_sources") or [])) or "無"
        if tok:
            rows.append(
                "| Token（模型輸出，僅 Claude／Codex） | %d | 輸入含大量重複 context，不拿來比；沒有用量的來源：%s |"
                % (tok, miss))
        else:
            rows.append("| Token | 本機掃不到 | 有用量紀錄的來源：%s；沒有的來源：%s |" % (src, miss))
        L += rows
        L.append("")

    L += ["## 工具使用（只算本人操作）", ""]
    L += ["總呼叫 %d 次，用到 %d 種工具，其中 MCP／外掛工具佔 %.1f%%。"
          % (h["tool_calls"], h["unique_tools"], h["mcp_ratio"] * 100), ""]
    L += ["| 工具 | 次數 |", "| :-- | --: |"]
    for k, v in list(h["top_tools"].items())[:15]:
        L.append("| `%s` | %d |" % (k, v))
    L.append("")

    b = s["behaviour_signals"]
    L += ["## 行為訊號", "", "> %s" % b["_note"], ""]
    L += ["| 訊號 | 次數 | 這個數字回答什麼 |", "| :-- | --: | :-- |"]
    L += ["| 交辦時給了條件或驗收 | %d | 有沒有把完成標準說出來 |" % b["spec_turns"],
          "| 指出問題要求修正 | %d | 是「換句話重問」還是「指出具體問題」，要看案例原文 |" % b["correction_turns"],
          "| 要求查證或核對 | %d | 有沒有把查核當成流程的一部分 |" % b["verify_turns"],
          "| 實際跑了測試／diff／lint | %d | 查核有沒有真的執行，不只是嘴上說 |" % b["verify_commands"],
          "| 三輪以上的對話 | %d | 單發任務 vs 迭代推進 |" % b["multi_turn_sessions"],
          "| 呼叫 subagent／委派工具 | %d | 有沒有分工 |" % b["delegate_tool_calls"], ""]

    a = s["artifacts"]
    L += ["## 產出與沉澱", ""]
    L += ["本人操作期間寫入 %d 個檔案，其中 %d 個落在可複用位置"
          "（SKILL.md、scripts/、workflows/、設定檔）。" % (a["files_written"], a["durable_write_count"]), ""]
    for p in a["durable_writes"][:25]:
        L.append("- `%s`" % p)
    L.append("")

    au = s["automation_evidence"]
    L += ["## 自動化證據（本人不在場時跑的）", "", "> %s" % au["_note"], ""]
    L += ["自動化對話 %d 則，橫跨 %d 天，工具呼叫 %d 次，寫入 %d 個檔案；子代理對話 %d 則。"
          % (au["sessions"], au["active_days"], au["tool_calls"], au["files_written"], au["subagent_sessions"]), ""]
    if au["distinct_entrypoints"]:
        L += ["驅動入口：" + "、".join("`%s`" % x for x in au["distinct_entrypoints"]), ""]
    if au["top_tools"]:
        L += ["常用工具：" + "、".join("%s×%d" % (k, v) for k, v in au["top_tools"].items()), ""]

    g = s["automation_gears"]
    L += ["## 自動化齒輪覆蓋度", "", "> %s" % g["_note"], ""]
    L += ["本期間觀察到 %d／5 顆齒輪。" % g["observed_count"], ""]
    L += ["| 齒輪 | 這顆在做什麼 | 本期間 | 在哪看到 |", "| :-- | :-- | :-- | :-- |"]
    for key, d0 in g["detail"].items():
        seen = d0["seen_in"]
        status = "**已觀察到**" if seen else "未觀察到"
        where = "、".join(seen) if seen else "—"
        L.append("| %s | %s | %s | %s |" % (d0["name"], d0["what"], status, where))
    L.append("")
    for key, d0 in g["detail"].items():
        if d0["evidence"]:
            L.append("**%s** 的證據：" % d0["name"])
            L.append("")
            for e in d0["evidence"]:
                L.append("- %s" % e)
            L.append("")
    if g["not_observed"]:
        L += ["未觀察到的齒輪只代表本期間沒讀到痕跡。要判斷「是不需要」還是「不會」，"
              "得看那個人的工作有沒有對應的複用需求——這一題證據包答不了，交給分析階段。", ""]

    d = s["sample_description_only"]
    L += ["## 樣本長相（只描述，不評分）", ""]
    L += ["本人單則發言長度中位數 %d 字，P90 %d 字。" % (d["user_msg_len_p50"], d["user_msg_len_p90"]), ""]
    L += ["_%s_" % d["_note"]]
    return "\n".join(L)


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description="掃描本機 AI 對話紀錄，產出證據包")
    ap.add_argument("--days", type=int, help="往前抓幾天（與 --since 擇一），預設 14")
    ap.add_argument("--since", help="起始日 YYYY-MM-DD")
    ap.add_argument("--until", help="結束日 YYYY-MM-DD，預設今天")
    ap.add_argument("--out", help="輸出目錄，預設 evidence/<起日>_<迄日>")
    ap.add_argument("--source", default="all",
                    help="claude-code,codex,antigravity 或 all（有裝才掃，沒裝就略過）")
    ap.add_argument("--cases", type=int, default=8, help="本人案例抽樣數，預設 8")
    ap.add_argument("--no-content", action="store_true", help="不輸出任何原文，只出計數")
    ap.add_argument("--claude-root", default=os.path.join(HOME, ".claude"))
    ap.add_argument("--codex-root", default=os.path.join(HOME, ".codex"))
    args = ap.parse_args()

    tz = dt.datetime.now().astimezone().tzinfo
    until = dt.datetime.combine(
        dt.date.fromisoformat(args.until) if args.until else dt.date.today(),
        dt.time.max, tzinfo=tz)
    if args.since:
        since = dt.datetime.combine(dt.date.fromisoformat(args.since), dt.time.min, tzinfo=tz)
    else:
        days = args.days or 14
        since = dt.datetime.combine(until.date() - dt.timedelta(days=days - 1), dt.time.min, tzinfo=tz)

    wanted = ({x.strip() for x in args.source.split(",")}
              if args.source != "all" else {"claude-code", "codex", "antigravity"})
    sessions, used = [], []
    if "claude-code" in wanted and os.path.isdir(args.claude_root):
        got = load_claude_code(args.claude_root, since, until)
        sessions += got
        used.append({"name": "claude-code", "root": redact(args.claude_root), "sessions": len(got)})
    if "codex" in wanted and os.path.isdir(args.codex_root):
        got = load_codex(args.codex_root, since, until)
        sessions += got
        used.append({"name": "codex", "root": redact(args.codex_root), "sessions": len(got)})
    if "antigravity" in wanted:
        got = load_antigravity(since, until)
        if got or os.path.isdir(os.path.join(HOME, ".gemini", "antigravity")):
            sessions += got
            used.append({
                "name": "antigravity",
                "root": redact(os.path.join(HOME, ".gemini", "antigravity")),
                "sessions": len(got),
            })
    if not used:
        print("找不到可讀的紀錄目錄，檢查 --claude-root / --codex-root，"
              "或見 references/log-sources.md。", file=sys.stderr)

    out = args.out or os.path.join("evidence", "%s_%s" % (since.date(), until.date()))
    os.makedirs(out, exist_ok=True)

    summary = build_summary(sessions, since, until, used)
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out, "metrics.md"), "w", encoding="utf-8") as fh:
        fh.write(render_metrics(summary) + "\n")
    with open(os.path.join(out, "cases.md"), "w", encoding="utf-8") as fh:
        fh.write(render_cases(sessions, args.cases, not args.no_content) + "\n")

    sp, h = summary["session_split"], summary["human_usage"]
    ef = summary.get("effort") or {}
    print("證據包完成：%s" % out)
    print("  本人對話 %d 則、發言 %d 次（自動化 %d、子代理 %d）｜工具呼叫 %d 次｜"
          "寫入檔案 %d 個｜可複用資產 %d 個"
          % (sp["human"], h["user_messages"], sp["automation"], sp["subagent"], h["tool_calls"],
             summary["artifacts"]["files_written"], summary["artifacts"]["durable_write_count"]))
    if ef.get("tokens_output"):
        print("  Token 輸出 %d（僅 %s；%s 掃不到）"
              % (ef["tokens_output"],
                 ",".join(ef.get("tokens_from_sources") or []) or "無",
                 ",".join(ef.get("tokens_unavailable_sources") or []) or "無"))
    if sp["human"] == 0:
        print("  這個期間沒有本人操作的紀錄。分析階段請寫「無法定級」，不要拿 LV0 當預設。")


if __name__ == "__main__":
    main()
