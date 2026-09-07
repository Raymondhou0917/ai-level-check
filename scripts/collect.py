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
    "Caveat:", "[Request interrupted", "[No response requested]", "API Error",
    "<bash-input>", "<bash-stdout>", "<bash-stderr>", ">>> TRANSCRIPT",
)
NOISE_CONTAINS = (
    "# CLAUDE.md", "# AGENTS.md instructions", "<INSTRUCTIONS>",
    "<user_instructions>", "<environment_context>", "<permissions instructions>",
    "Codebase and user instructions are shown below",
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
DELEGATE_TOOLS = {"Agent", "Task", "SendMessage"}

HUMAN, AUTOMATION, SUBAGENT = "human", "automation", "subagent"


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

    def touch(self, ts):
        if not ts:
            return
        if self.started is None or ts < self.started:
            self.started = ts
        if self.ended is None or ts > self.ended:
            self.ended = ts

    def note_write(self, path):
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


def iter_jsonl(path):
    try:
        with open(path, "r", errors="ignore") as fh:
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
            if typ == "assistant" and msg.get("model"):
                sess.models[msg["model"]] += 1
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

    h_msgs = [t for s in human for _, t in s.user_msgs]
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
        "human_usage": {
            "sessions": len(human),
            "sessions_with_tools": sum(1 for s in human if s.tools),
            "active_days": len(h_days),
            "user_messages": len(h_msgs),
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
            "_note": "訊號＝出現過的次數。出現不等於做得好，沒出現不等於不會，判斷交給分析階段讀案例原文。",
            "spec_turns": count_hits(h_msgs, SPEC_HINTS),
            "correction_turns": count_hits(h_msgs, CORRECTION_HINTS),
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
        "sample_description_only": {
            "_note": "只描述樣本長相，不評分。短提問不是弱點，長提問也不是能力。",
            "user_msg_len_p50": pct(0.5),
            "user_msg_len_p90": pct(0.9),
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
    if count_hits(texts, CORRECTION_HINTS):
        sc += 6
    if count_hits(texts, SPEC_HINTS):
        sc += 4
    return sc


def render_one_case(idx, s, with_content):
    out = []
    label = os.path.basename(redact(s.cwd or "")) or "未標示專案"
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
    corr = [t for t in texts if any(h.lower() in t.lower() for h in CORRECTION_HINTS)]
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

    h = s["human_usage"]
    L += ["## 本人操作的範圍", "", "| 項目 | 數字 |", "| :-- | --: |"]
    L += ["| 對話數 | %d |" % h["sessions"],
          "| 其中有實際動手（有工具呼叫） | %d |" % h["sessions_with_tools"],
          "| 有紀錄的天數 | %d |" % h["active_days"],
          "| 使用者發言 | %d |" % h["user_messages"],
          "| 平台明確標成「人打的」 | %d |" % h["platform_marked_human"],
          "| 涵蓋專案 | %d |" % len(h["projects"]), ""]
    L += ["模型：" + ("、".join("%s×%d" % (k, v) for k, v in h["models"].items()) or "紀錄未標示"), ""]

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
    ap.add_argument("--source", default="all", help="claude-code,codex 或 all")
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
              if args.source != "all" else {"claude-code", "codex"})
    sessions, used = [], []
    if "claude-code" in wanted and os.path.isdir(args.claude_root):
        got = load_claude_code(args.claude_root, since, until)
        sessions += got
        used.append({"name": "claude-code", "root": redact(args.claude_root), "sessions": len(got)})
    if "codex" in wanted and os.path.isdir(args.codex_root):
        got = load_codex(args.codex_root, since, until)
        sessions += got
        used.append({"name": "codex", "root": redact(args.codex_root), "sessions": len(got)})
    if not used:
        print("找不到可讀的紀錄目錄，檢查 --claude-root / --codex-root，"
              "或見 references/log-sources.md。", file=sys.stderr)

    out = args.out or os.path.join("evidence", "%s_%s" % (since.date(), until.date()))
    os.makedirs(out, exist_ok=True)

    summary = build_summary(sessions, since, until, used)
    with open(os.path.join(out, "summary.json"), "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out, "metrics.md"), "w") as fh:
        fh.write(render_metrics(summary) + "\n")
    with open(os.path.join(out, "cases.md"), "w") as fh:
        fh.write(render_cases(sessions, args.cases, not args.no_content) + "\n")

    sp, h = summary["session_split"], summary["human_usage"]
    print("證據包完成：%s" % out)
    print("  本人對話 %d 則（自動化 %d、子代理 %d）｜工具呼叫 %d 次｜"
          "寫入檔案 %d 個｜可複用資產 %d 個"
          % (sp["human"], sp["automation"], sp["subagent"], h["tool_calls"],
             summary["artifacts"]["files_written"], summary["artifacts"]["durable_write_count"]))
    if sp["human"] == 0:
        print("  這個期間沒有本人操作的紀錄。分析階段請寫「無法定級」，不要拿 LV0 當預設。")


if __name__ == "__main__":
    main()
