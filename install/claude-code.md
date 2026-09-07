# 安裝：Claude Code

## 個人（一台電腦）

```bash
git clone https://github.com/Raymondhou0917/ai-level-check.git ~/ai-level-check
ln -s ~/ai-level-check ~/.claude/skills/ai-level-check
```

用 symlink 的好處是之後 `git pull` 就跟著更新，不用重裝。

不想放 clone 目錄的話，直接複製：

```bash
mkdir -p ~/.claude/skills/ai-level-check
cp -R SKILL.md references scripts ~/.claude/skills/ai-level-check/
```

## 用法

```
/ai-level-check
```

或直接講：

```
幫我跑這兩週的 AI 使用檢核
分析我這個月怎麼用 AI，我想知道我是哪一型
```

只想先看數字、不要完整報告：

```bash
python3 ~/.claude/skills/ai-level-check/scripts/collect.py --days 14
```

跑完會在當前目錄產生 `evidence/`，直接看 `metrics.md` 就好。

## 確認裝好了

```bash
ls ~/.claude/skills/ai-level-check/SKILL.md
python3 ~/.claude/skills/ai-level-check/scripts/collect.py --days 7 --no-content --out /tmp/aif-check
```

第二行如果印出「本人對話 N 則」就是通了。印出 0 則的話，
先確認 `~/.claude/projects/` 底下有沒有東西，再看 [references/log-sources.md](../references/log-sources.md)。

## 團隊部署

要在每台公司電腦上預設裝好，見 [team-deploy.md](team-deploy.md)。
**裝之前請先讀 [references/privacy.md](../references/privacy.md)。**
