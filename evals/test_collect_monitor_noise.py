#!/usr/bin/env python3
import json
import pathlib
import runpy
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECT = ROOT / "scripts" / "collect.py"
HUMAN = "這是真人打的：請只改 collect.py。"
NOISE_A = "<task-notification>\n<task-id>abc</task-id>\nmonitor ping"
NOISE_B = "[SYSTEM NOTIFICATION - NOT USER INPUT]\nbackground watcher"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        claude_root = tmp / "claude"
        session = claude_root / "projects" / "fixture" / "monitor.jsonl"
        session.parent.mkdir(parents=True)
        records = [
            {
                "type": "user",
                "timestamp": "2026-09-08T12:00:00+08:00",
                "entrypoint": "cli",
                "origin": {"kind": "human"},
                "message": {"content": HUMAN},
            },
            {
                "type": "user",
                "timestamp": "2026-09-08T12:00:05+08:00",
                "entrypoint": "cli",
                "origin": {"kind": "human"},
                "message": {"content": NOISE_A},
            },
            {
                "type": "user",
                "timestamp": "2026-09-08T12:00:10+08:00",
                "entrypoint": "cli",
                "origin": {"kind": "human"},
                "message": {"content": [{"type": "text", "text": NOISE_B}]},
            },
            {
                "type": "assistant",
                "timestamp": "2026-09-08T12:00:11+08:00",
                "message": {"content": "ok"},
            },
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
        assert summary["human_usage"]["user_messages"] == 1
        assert HUMAN in cases
        assert "<task-notification" not in cases
        assert "SYSTEM NOTIFICATION" not in cases


if __name__ == "__main__":
    main()
