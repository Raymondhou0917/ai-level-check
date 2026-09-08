[繁體中文](README.md) · **English**

<div align="center">

# AI 幾級了 ai-level-check

### How good is your AI usage, really? Let AI read the record.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.5-brightgreen.svg)](CHANGELOG.md)
[![Sources](https://img.shields.io/badge/sources-Claude_Code_%7C_Codex_%7C_Antigravity-blue.svg)](references/log-sources.md)
[![zh-TW](https://img.shields.io/badge/zh--TW-Taiwan-e4002b.svg)](README.md)
[![en](https://img.shields.io/badge/en-English-1b6ca8.svg)](README.en.md)
[![No Ranking](https://img.shields.io/badge/no-ranking%20%C2%B7%20no%20percentile-lightgrey.svg)](references/privacy.md)

<br>

Let AI evaluate your AI usage. Do not let people guess.<br>
The most accurate way is to let AI read AI’s own logs.

<br>

<table>
<tr><td align="left">

🧑‍💼 &nbsp;A manager asks “have you been using AI?” and only hears “yeah, it’s great.”<br>
📄 &nbsp;A team fills an AI-skills survey with the version of themselves they wish were true.<br>
🎓 &nbsp;After a course, students still cannot tell if they actually got better.<br>
💼 &nbsp;In an interview, install this skill, run a report, and screen-share. No more “I use AI a lot lately.”

</td></tr>
</table>

### ✨ `AI 幾級了.skill` is built for those moments.

<br>

It scans the logs Claude Code, Codex, and Antigravity already left on disk:
how this person delegated, which tools they called, how they corrected mistakes, and what they shipped.
Then it writes a **case-backed, traceable** AI-usage report.

**LV0–LV5 usage levels · org-strength and maturity · four system checks · 16 usage personas · one printable HTML report**

Works with Claude Code, Codex, Cursor, and any agent that can read Markdown.

<br>

**First confirm what was read → then judge what showed up → only then say what to change**

This is not an AI giving people a score. It lays the evidence on the table so people can see it themselves.

</div>

---

## See it first

The four screenshots below are from a real 14-day report (2026-08-26 to 09-08). To scroll a full page and switch levels, open the public demo:

[AI 幾級了 Demo](https://ai.lifehacker.tw/reports/ai-level-check-demo/)

The live demo is in Traditional Chinese. The layout, levels, and how a report argues are the same.

<table>
<tr>
<td width="50%"><img src="docs/screenshots/01-overview.jpg" alt="Overview: LV5, strengths, gaps, next step"></td>
<td width="50%"><img src="docs/screenshots/02-usage.jpg" alt="Where AI was actually used in these 14 days"></td>
</tr>
<tr>
<td><img src="docs/screenshots/03-evaluation.jpg" alt="Why this level, plus the PVSE persona"></td>
<td><img src="docs/screenshots/04-system.jpg" alt="One shared rule layer across four AI entry points"></td>
</tr>
</table>

The screenshots are real fragments from a report Raymond ran himself. The [demo site](https://ai.lifehacker.tw/reports/ai-level-check-demo/) is simulated data.

| Demo | Level | What this person does |
| :-- | :-- | :-- |
| [Demo 1 · LV1](https://ai.lifehacker.tw/reports/ai-level-check-demo/lv1.html) | Rephrase and ask again | Web chat only; if it feels wrong, ask again |
| [Demo 2 · LV3](https://ai.lifehacker.tw/reports/ai-level-check-demo/lv3.html) | Precise delegation | Clear briefs, names the error, verifies; no reusable template yet |
| [Demo 3 · LV4](https://ai.lifehacker.tw/reports/ai-level-check-demo/lv4.html) | Modular use | The method is a skill, a little scheduling; the system does not run itself |

---

## How do I use「AI 幾級了」?

Two kinds of people, two paths. Processing happens **on your machine**, or in the web chat you already use. **Nothing is sent to this project, and nothing is sent to Raymond.**

### 1. You already have an AI agent

Claude Code, Codex, Cursor, Antigravity: install the skill, then say “run an AI-usage review for the last two weeks.” It scans logs and writes the report on your computer.

```bash
git clone https://github.com/Raymondhou0917/ai-level-check.git ~/ai-level-check
ln -s ~/ai-level-check ~/.claude/skills/ai-level-check
```

Other entry points: [Claude Code](install/claude-code.md), [Codex](install/codex.md), [Cursor](install/cursor.md).

Numbers only, no full report:

```bash
python3 ~/ai-level-check/scripts/collect.py --days 14
```

Standard library only. No packages, no network, no upload.

### 2. You only use ChatGPT or Gemini in the browser

Open [prompts/chat-paste.md](prompts/chat-paste.md) and paste the prompt. It includes the public repo URL so the model can fetch the criteria.

- If this thread already has your work: say “evaluate me from this thread and write the report now”
- If this is a blank chat: paste recent threads, then tell it to write
- **Do not say “make one like the demo.”** The demos are fictional people. Layout comes from `templates/report-skeleton.html`. A report without the 16-type persona block (four-letter code + 2×2 axes) is incomplete.

Most web AIs (including Gemini) cannot see other chats. Do not only say “use your memory of me.” This path usually tops out at LV3. Not weaker — the browser cannot see the system on disk.

---

## Interviews: let the log speak

The old interview question is “how good are you with AI?”
Even a polished answer cannot tell you whether they used it, or crammed two days before.

Now it can be three steps:

1. Ask the candidate to install this skill **on their own computer**
2. Have them run a report for the last two weeks
3. They screen-share, or you look at the report on their machine

You see how they delegate, whether they verify, and whether they leave anything reusable — not a story they invented in the room.

Three hard rules if you use it this way:

- **They run it themselves.** The interviewer does not run it for them, and does not ask them to zip `~/.claude/` and email it.
- **Screen-share only. Do not ask for the HTML file. Do not keep screenshots.** The report may contain current clients or unreleased work.
- **This report cannot be the sole reason to hire or reject.** People who only use ChatGPT in the browser often have no local logs. That is a source difference, not weaker ability.

The full privacy boundary is in [references/privacy.md](references/privacy.md).

---

## Why AI should be the one judging

People judging people fail in three ways: **they cannot see, they cannot remember, and they have a mood.**

A manager cannot see the eight midnight retries that fixed a bug.
They only see a three-minute update in the weekly meeting.
They forget what you looked like three months ago.
And today’s mood changes how they read what you handed in.
Interviews are the same: do not trust “I have been using AI a lot.” The log will talk.

AI does not have those three problems. It can read every thread, hold the whole window, and has no opinion about you.

The fourth problem is worse: **people are bad at judging AI ability in the first place.**

Ability is not whether someone can say “prompt engineering.”
It is whether they give a done-standard when they delegate, whether they can point at the exact error when the model is wrong, and whether they leave something the next similar job can reuse.
All of that lives in the dialogue log. Only something that can finish reading those logs can judge it.

> **Let AI evaluate your AI usage. Do not let people guess.**<br>
> **The most accurate way is to let AI read AI’s own logs.**

---

## What it reads, and what it writes

The local skill scans agent logs already on your disk and writes a single HTML report. The script does not go online. Raw threads are not uploaded to this project. Raymond cannot see them.

If you already use a cloud LLM, those chats already go through that vendor’s cloud. This tool does not open a second path that sends data to us.

The pipeline diagram is in [docs/how-it-works.md](docs/how-it-works.md). Privacy rules: [references/privacy.md](references/privacy.md). Skill files are in Traditional Chinese; any capable agent can follow them.

---

## The one thing that decides if the report is true: separate human typing from machine typing

This only showed up in implementation, and it decides whether the whole report is valid.

`~/.claude/projects/` holds two things that look identical: words you typed at the keyboard, and **system prompts your own bot emitted at 3 a.m.**

Without the split, the same machine and the same 14 days (measured 2026-09) look like this:

| | Unsplit | Split, `human` only |
| :-- | --: | --: |
| Threads | 1,255 | **42** (plus automation 1,207, subagent 6) |
| Median “user message” length | 16,536 characters | **120** |
| “Gave conditions when delegating” | 1,214 | **17** |

The left column is not how this person types. Those 16,536 characters are a bot’s system prompt.
If you analyse “how this person prompts” from the left column, every conclusion is wrong.

So `collect.py` splits every thread by platform fields:

| Type | What it is | How it is used |
| :-- | :-- | :-- |
| `human` | Typed at the keyboard | **Prompting behaviour uses this class only** |
| `automation` | Driven by a program or schedule they wrote | Not prompting; counts as LV4–LV5 implementation evidence |
| `subagent` | A child agent dispatched by a parent thread | A clue about division of labour |

Automation is not noise. It answers a rarer question:
**does the thing they built keep running when they are not in the room?**

Criteria and measured field distributions: [references/log-sources.md](references/log-sources.md).

---

## Usage levels LV0–LV5

| Level | Name | In one line |
| :-- | :-- | :-- |
| **LV0** | Trust the answer | A task that needed conditions or a check was accepted as-is |
| **LV1** | Rephrase and retry | They notice errors and push forward by asking again |
| **LV2** | Single-point use | One class of work can be finished stably; they can tell if an answer is usable |
| **LV3** | Precise delegation | They give background, scope, and a done-standard; they can name the concrete error |
| **LV4** | Modular use | A working method is fixed as a template, skill, or agent, and tested before it is trusted |
| **LV5** | System operations | Division of labour, exception handling, maintenance, and write-back are one system; if they depend on a cloud LLM, two entry points must read the same rules |

Three hard rules:

- **LV0 is not the default when data is missing.** No logs means “cannot be leveled.”
- **LV4–LV5 need implementation evidence.** Ideas, self-report, or the model claiming it is done do not count.
- **Unobserved is not cannot.** If a higher level did not show up in this window, say that. Do not say they cannot.

Full criteria: [references/levels.md](references/levels.md).

### Automation gears: after they leave the keyboard, is anything still happening?

“Do you use automation?” always gets “yeah, I do.”
So the report looks for five concrete triggers. Those are the only ways a modern system makes something happen by itself:

```
What should happen without you sitting there?
│
├─► “every day at 9, or every few hours”     └── ① time   Cron / launchd
├─► “something outside moved (form, pay, comment)” └── ② webhook / n8n
├─► “the moment you open the agent or commit” └── ③ lifecycle hook
├─► “push to GitHub and it tests, packs, ships” └── ④ CI / CD
└─► “if the bot dies, restart it and tell me” └── ⑤ supervisor / heartbeat
```

All five leave traces on disk. No survey. Scan the existing logs.

> **Coverage is not a score.** Using all five is not better than using two well. A writer often only needs ① and ②.
> **Unobserved is not cannot** — a gear set up three months ago and still running may not be touched in this window.

A pitfall worth writing down: the first detector grepped for keywords and hit 5/5, because the “evidence” was `rg -n -i "…webhook…"`. That is **searching** for webhook, not **running** one.
After the rule became “count doing, not mentioning,” the same data became 3/5, and each hit pointed at a real artifact.
**A detector that false-positives is more dangerous than no detector**, because it produces fake evidence that looks sourced.

Details: [references/automation-gears.md](references/automation-gears.md).

### Four system checks (scored separately from the level)

The level answers “what usage showed up.” The checks answer “which parts of this setup were **actually tested**”:

1. Can a stranger finish the work from the docs alone?
2. When data is wrong or missing, does the system stop and report, or invent a wrong answer?
3. With nobody watching, does automation keep doing the right thing?
4. Can a successor find the owner, the version, the acceptance bar, and the reporting window?

Passing all four does not auto-promote to LV5. Skipping a check does not auto-demote.

---

## 16 AI-usage personas

This layer is for workshops and classrooms. It is also the only layer that is safe to share in public.

Four axes. Each letter needs evidence in the log:

```
  Brief     P  enough context ──────── Q  ask first
  Check     V  verify by hand ──────── A  accept as-is
  Keep      S  leave an asset ──────── O  one-off
  Hands     E  let AI execute ──────── C  chat only
```

| | Enough context P | | Ask first Q | |
| :-- | :-- | :-- | :-- | :-- |
| | **Verify V** | **Accept A** | **Verify V** | **Accept A** |
| **Keep S ＋ execute E** | System architect | Automation maniac | Fix-it-as-you-go | All-in |
| **Keep S ＋ chat C** | Process designer | Delegating manager | Curious fact-checker | Idea stenographer |
| **One-off O ＋ execute E** | Precise operative | Efficiency outsourcer | Instinct experimenter | Wishing well |
| **One-off O ＋ chat C** | Proof-seeker | Spec writer | Sparring partner | Chat companion |

> **A persona is a style, not a score.** `QAOC` (chat companion) is not weaker than `PVSE` (system architect).
> They put AI in different places. A `QAOC` can be LV3; a `PVSE` can still be LV2.
>
> The report must say this every time a persona appears. The moment a persona is read as a score, the report will be used for the wrong job.

Each type: [references/personas.md](references/personas.md).

---

## Privacy: things this project is written not to do

This tool reads what someone types at work. Technically it could become surveillance.
What stops that is policy, not code. These are locked in the rules:

| It will not | Why |
| :-- | :-- |
| Rank, percentile, “better than X% of people” | There is no verifiable global database of AI-usage ability. Those numbers would be invented |
| Remotely scan employees’ logs | `collect.py` only reads the local disk. A team view means each person runs it themselves |
| Auto-push or auto-upload | That skips “the person has seen it” |
| Treat prompt length, turn count, or tool count as ability | Short prompts are not weakness. Long prompts are not skill |
| Plug into automated HR decisions | This is an observation report, not a performance tool |

> **This report cannot be the sole basis for performance review, promotion, firing, or transfer.**

What to tell a team before rollout: [references/privacy.md](references/privacy.md) and [install/team-deploy.md](install/team-deploy.md).

---

## Install notes by platform

How to run it is above. Extra notes per entry point:

| Platform | Doc |
| :-- | :-- |
| Claude Code | [install/claude-code.md](install/claude-code.md) |
| Codex | [install/codex.md](install/codex.md) |
| Cursor / other agents | [install/cursor.md](install/cursor.md) |
| Browser chat only | [prompts/chat-paste.md](prompts/chat-paste.md) |
| Team rollout | [install/team-deploy.md](install/team-deploy.md) |

### Layout

```
ai-level-check/
├── SKILL.md                        seven-step flow (Traditional Chinese)
├── scripts/collect.py              local collector
├── scripts/publish.sh              push a report to a private repo
├── references/                     criteria (Traditional Chinese)
├── prompts/chat-paste.md           paste-mode prompt
├── templates/report-skeleton.html  printable single-file report
├── docs/                           fictional public demo
├── evals/report-checklist.md       19 “did the report follow the rules” checks
└── install/                        Claude Code · Codex · Cursor · team
```

---

## FAQ

### I only use ChatGPT in the browser

Open [prompts/chat-paste.md](prompts/chat-paste.md). If this thread already has your work, tell it to write; if the chat is blank, paste records first.

This path judges the Q&A you pasted. It cannot see schedules, draft mailboxes, or local scripts.
The report will state its scope. The level usually tops out at LV3. LV4 / LV5 still need the local skill.

Do not paste the whole `SKILL.md` into a web chat. That file is for an agent that can scan the disk.

### It says I am LV2, but I know I do more

That can be correct, and the report should say so itself.

“Unobserved” is not “cannot.” If the higher-level work happened where there is no log (browser, whiteboard, spoken briefs), the right wording is
“confirmed up to LV2; higher levels not yet evaluated,” not “you are only LV2.”

If a report writes the latter, file a [misjudgement issue](.github/ISSUE_TEMPLATE/misjudgement.md).

### Can a company use this to review me?

The rules say no: not as the sole performance basis, no ranking, no automated HR.

Rules cannot stop a company that is determined to misuse it. The real defense is the rollout:
**voluntary, they run it, they decide whether to push.** If a rollout rejects those three, you can reasonably doubt the goal is growth.

### Can I ask interview candidates to run this?

Yes. That is exactly where it beats a spoken self-report. They install it, they run it, they screen-share.
No file, no screenshot, not the sole hiring criterion.

People on browser-only chat, or a locked-down work laptop, often have no local logs —
use [paste mode](prompts/chat-paste.md). Do not call them weaker. Full boundary: [references/privacy.md](references/privacy.md).

### Why is there no total score?

Because an honest total score cannot be computed.

Ability, stability, evidence strength, and what to fix next are four different rulers.
Force them into one number and that number becomes the only thing anyone looks at, and then everyone starts optimizing the number.

The report gives a level (a behaviour threshold, not a score), a persona (a style), and observations that point at cases. Those three beat one number.

### My logs have client data. Can I still run it?

Yes, with `--no-content`:

```bash
python3 scripts/collect.py --days 14 --no-content
```

The report will have counts and behaviour notes, no quoted text.
The default mode also redacts home paths, emails, phone numbers, and common key shapes. That is a floor, not a guarantee.

### Why 16 types? Isn’t MBTI unscientific?

Because it is useful here, not because it is science.

The persona’s job is **to get a group of people talking.** The criteria that actually judge are LV0–LV5 and the four system checks. Those require cases. The persona is a shell that makes the conversation possible, which is why we forbid reading it as a score.

The most valuable team use is not “what type are you.” It is “our whole team leans `A` (no verification).” That is worth more than any one person’s level.

---

## Contribute

This project only becomes general when people in other jobs add their own criteria.

How an engineer uses AI is not how marketing, design, support, or accounting uses it. One person cannot write criteria for every role.

The two contributions we need most:

- **Collectors for new sources.** Cursor and internal tools are still missing. Antigravity is already wired.
  A PR needs measured field distributions. Guessed fields poison every judgement downstream.
- **Domain criteria.** In your job, what does “using it well” look like in the log?

Unfinished work is listed in [ROADMAP.md](ROADMAP.md) (Traditional Chinese; English PRs are fine).
Read [CONTRIBUTING.md](CONTRIBUTING.md) first. We explicitly reject ranking, central scanning, and writing personas as a hierarchy.

---

## Author

This project is by [Raymond Hou (雷蒙)](https://raymondhouch.com/).
He runs 雷蒙三十: digital work practice, AI usage, solopreneurship.

- **[Academy](https://academy.lifehacker.tw/)** — courses
- **[AI Agent resources](https://cc.lifehacker.tw/)** — Claude Code and Codex, including for non-engineers
- **[Weekly letter](https://lifehacker.kit.com/ai-agent)** — one email a week
- **[Personal manual](https://raymondhouch.com/lifehacker/raymond-manual/)**

Also on [Facebook](https://www.facebook.com/raymondhou0917/), [Instagram](https://www.instagram.com/yuiraymond/), and [Threads](https://www.threads.com/@raymond0917).

The project stays free. A star is nice.
What actually makes it better is a [misjudgement report](.github/ISSUE_TEMPLATE/misjudgement.md), or criteria from your own job.

---

## Credits

This tool was drafted by [Chen Jing-ru of Inorder Studio](https://www.inorder.studio/), then fully expanded and open-sourced by [Raymond Hou (雷蒙)](https://raymondhouch.com/). It started over a meal: how does a company know where a team’s AI ability actually is? Surveys are unreliable; spoken reports are worse. The conclusion was that AI should read AI’s usage logs — a [review prompt](https://inorders.notion.site/ai-prompt) you can paste into an AI, plus a Skill that runs and writes a report. Raymond added local multi-agent logs, a split between human and machine text, usage personas, automation-level review, and git pinning for each period.

---

## License

[MIT License](LICENSE). Fork, change, send a PR.
