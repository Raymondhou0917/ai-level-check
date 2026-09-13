#!/usr/bin/env python3
"""Claude Code 以 user 身分寫入、但不是本人打的字，不能算進發言與修正（#4）。"""
import json
import pathlib
import runpy
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECT = ROOT / "scripts" / "collect.py"
HUMAN_FIRST = "這是真人打的：幫我整理 collect.py 的雜訊規則。"
HUMAN_FIX = "不對，漏了 compact 摘要，請再改一次。"
COMPACT = ("This session is being continued from a previous conversation that ran out of context. "
           "Summary: 使用者說錯了，要求重來。")
SKILL_BODY = "Base directory for this skill: /tmp/skills/design\n\nApproach this as the design lead at a small studio."
SKILL_PROMPT = "Approach this as the design lead at a small studio known for their versatility. 不對就重來。"
CONTINUE = "Continue from where you left off."


def user(ts, content, **flags):
    rec = {"type": "user", "timestamp": ts, "entrypoint": "cli", "message": {"content": content}}
    rec.update(flags)
    return rec


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        claude_root = tmp / "claude"
        session = claude_root / "projects" / "fixture" / "injected.jsonl"
        session.parent.mkdir(parents=True)
        records = [
            user("2026-09-08T12:00:00+08:00", HUMAN_FIRST),
            # 新版：有旗標
            user("2026-09-08T12:01:00+08:00", COMPACT, isCompactSummary=True, isVisibleInTranscriptOnly=True),
            user("2026-09-08T12:02:00+08:00", [{"type": "text", "text": SKILL_PROMPT}], isMeta=True),
            user("2026-09-08T12:03:00+08:00", CONTINUE, isMeta=True),
            # 舊版：沒有旗標，只能靠開頭字串
            user("2026-09-08T12:04:00+08:00", COMPACT),
            user("2026-09-08T12:05:00+08:00", [{"type": "text", "text": SKILL_BODY}]),
            user("2026-09-08T12:06:00+08:00", HUMAN_FIX),
            {"type": "assistant", "timestamp": "2026-09-08T12:06:05+08:00", "message": {"content": "ok"}},
        ]
        session.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
                           encoding="utf-8")
        out = tmp / "evidence"
        old_argv = sys.argv
        try:
            sys.argv = [str(COLLECT), "--source", "claude-code",
                        "--claude-root", str(claude_root), "--codex-root", str(tmp / "codex"),
                        "--since", "2026-09-08", "--until", "2026-09-08", "--out", str(out)]
            runpy.run_path(str(COLLECT), run_name="__main__")
        finally:
            sys.argv = old_argv
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        cases = (out / "cases.md").read_text(encoding="utf-8")
        assert summary["session_split"]["human"] == 1
        assert summary["human_usage"]["user_messages"] == 2, summary["human_usage"]["user_messages"]
        assert summary["behaviour_signals"]["correction_turns"] == 1, summary["behaviour_signals"]
        assert HUMAN_FIRST in cases
        assert HUMAN_FIX in cases
        for noise in ("This session is being continued", "Approach this as the design lead",
                      "Base directory for this skill", "Continue from where you left off"):
            assert noise not in cases, noise


if __name__ == "__main__":
    main()
