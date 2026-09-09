#!/usr/bin/env python3
import json
import os
import pathlib
import runpy
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECT = ROOT / "scripts" / "collect.py"
MESSAGE = "繁體中文測試：驗證 UTF-8 原句。"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        claude_root = tmp / "claude"
        session = claude_root / "projects" / "fixture" / "utf8.jsonl"
        session.parent.mkdir(parents=True)
        records = [
            {
                "type": "user",
                "timestamp": "2026-09-08T12:00:00+08:00",
                "entrypoint": "cli",
                "origin": {"kind": "human"},
                "message": {"content": MESSAGE},
            },
            {
                "type": "assistant",
                "timestamp": "2026-09-08T12:00:01+08:00",
                "message": {"content": "ok"},
            },
        ]
        session.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
                           encoding="utf-8")
        out = tmp / "evidence"
        assert "PYTHONUTF8" not in os.environ
        assert "PYTHONIOENCODING" not in os.environ
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
        metrics = (out / "metrics.md").read_text(encoding="utf-8")
        assert summary["human_usage"]["user_messages"] == 1
        assert MESSAGE in cases
        assert "證據包計數" in metrics


if __name__ == "__main__":
    main()
