# ROADMAP

> 最後更新：2026-09-09
> 專案狀態：0.4.6。骨架能跑，來源覆蓋與報告呈現還有缺口。歡迎直接開 PR。

Unfinished work lives here so people do not duplicate effort. English PRs are welcome; this file is in Traditional Chinese because the rest of the maintainer notes are.

想幫忙的話，先讀 [CONTRIBUTING.md](CONTRIBUTING.md)。這份清單告訴你**現在缺什麼**；那份告訴你**什麼不收**。

一個 PR 做一件事。標題用 `[collector]` `[判準]` `[型錄]` `[文件]` `[修正]` `[呈現]`。

```
已公開 ──► 報告不要像分數 ──► 更多來源 ──► 判準更公平 ──► 團隊導入
  ✅              進行中              最需要 PR         先開 Issue         文件為主
```

---

## Phase 0：公開骨架 ✅

- [x] 本機 collector：Claude Code、Codex、Antigravity
- [x] 人機分流（human / automation / subagent）
- [x] LV0–LV5、四項系統驗證、16 型人物志、隱私紅線
- [x] 貼上模式（網頁版 Chat）
- [x] 公開 Demo：https://ai.lifehacker.tw/reports/ai-level-check-demo/
- [x] GitHub 公開 repo
- [x] 面試用法寫進 [`references/privacy.md`](references/privacy.md)（本人跑、螢幕分享、不留檔、不能當錄用單一依據）

**重要發現**：

- 不分流會把 bot 的 system prompt 當成這個人在打字。
- 齒輪只認做了、不認提到。誤報比沒有偵測器更糟。
- 分型是風格不是分數。任何讓 16 型看起來像排名的改動不會合併。

---

## Phase 1：報告呈現不要像分數（進行中）

這些改動不需要新資料來源。適合第一個 PR。

- [ ] **齒輪不要印 `3／5`。** 規則寫了「覆蓋度不是分數」，但分子分母一出現，附註就等於沒寫。改成五顆各自「本期間有觀察到／未出現／本職能不適用」。相關檔：[`references/automation-gears.md`](references/automation-gears.md)、報告骨架、README 裡當成果寫的 `3／5`。
- [ ] **總覽主標少用 `LV4＋`。** `＋` 會被讀成快到下一級。改用「目前可確認至 LVn」這類既有用語。相關檔：[`references/levels.md`](references/levels.md)、[`SKILL.md`](SKILL.md)、[`templates/report-skeleton.html`](templates/report-skeleton.html)。
- [ ] **第一屏不要放會被當成能力指標的數字。** 工具數、對話輪數、字數中位數可以在詳細分析，不要當總覽英雄數字。
- [ ] **靜默齒輪。** 三個月前設好、評估窗口內沒改過的 launchd／GitHub Actions，現在會不會整顆消失？請用真實機器驗證，把結果寫回 `automation-gears.md`。若會消失，總覽更不該印覆蓋率。

驗收：報告 HTML 與 Demo 的齒輪區塊看不到分數、進度條、雷達圖；README 示範句也不再用 `n／5`。

---

## Phase 2：來源覆蓋（最需要 PR）

目前本機掃得到 Claude Code、Codex、Antigravity。掃不到的來源，報告開頭必須明講，不能讓人以為這是全部。

- [ ] **Cursor collector。** 紀錄在 `~/Library/Application Support/Cursor/`（SQLite）。這是現在最缺的一塊。用 [new-source issue 模板](.github/ISSUE_TEMPLATE/new-source.md)，PR 必須附欄位分布實測數字與人機分流規則。
- [ ] **Gemini CLI collector。** 與 Antigravity 不是同一條路徑，不要混在一起猜。
- [ ] **ChatGPT／Claude 網頁版匯出檔。** 沒有本機 log 的人，現在只能貼上。若你有穩定的匯出格式，歡迎補一條離線匯入，仍須脫敏與人機分流。
- [ ] **公司內部 AI 工具。** 各做各的 collector，不要改核心判準去遷就單一廠商。

沒有實測數字的 collector 不會合併。猜出來的欄位會讓所有下游判斷一起錯。

面試遇到「我用 Cursor」時，現況就是報告偏空。在 collector 補上之前，文件要繼續把這件事講成**來源缺口，不是能力差**。相關檔：[`references/log-sources.md`](references/log-sources.md)、[`references/privacy.md`](references/privacy.md)。

---

## Phase 3：判準更公平（先開 Issue 再 PR）

這層會改變誰被判哪一級，請先開 Issue 把誤判案例寫清楚。

- [ ] **LV4 分得出「自己寫的 skill」和「裝來的 skill」嗎？** 現在 collector 認的是路徑與再次使用。[`evidence-rules.md`](references/evidence-rules.md) 已寫「這份 skill 本身不是本人能力的證據」，但裝一份官方 skill 再跑一次，會不會就被算成 LV4？需要實測，不能靠文件自證。
- [ ] **貼上模式／純網頁版會不會系統性偏 `C`、偏低 LV？** E／C 軸很容易變成「你用哪套工具」而不是「你習慣怎麼用」。若會，面試對這群人結構性不利，要在報告與 README 寫死，而不是默默扣級。
- [ ] **第二份、第 N 份真人樣本。** 現在完整跑過的真實職能太少。歡迎用 `--no-content` 跑完，把脫敏後的 `metrics.md` 觀察（不要貼原文）開成 Issue。16 型與 LV4／LV5 的區辨力，不能永遠只靠維護者自己的機器。
- [ ] **人物志名稱的中性。** 文件說 `QAOC` 不比 `PVSE` 差，型錄卻叫「系統建築師」對上「許願池／一把梭」。工作坊可以靠主持話術壓住，HTML 做不到。改名可以，但不能改成另一套隱含排序。硬規則見 CONTRIBUTING。
- [ ] **評估框架獨立於課程。** 五顆齒輪來自《超級 AI 個體》附錄。MIT 沒問題，但公司導入時會問這是通用評估還是課程行銷。README 致謝可留，判準要能在沒上過課的前提下被採用。

---

## Phase 4：團隊導入（文件為主）

- [ ] **把分支保護寫成團隊部署的必做，不是建議。** 「推上去就改不掉」成立的前提是禁止 force push、禁止 rewrite。[`install/team-deploy.md`](install/team-deploy.md) 現在只寫建議。
- [ ] **給別人看的預設走 `--no-content`。** 400 字摘錄仍可能識別客戶。主管版、面試版都該預設無原文。
- [ ] **分析階段拒絕「幫我比較這兩個人」「把等級寫進績效表」。** [`privacy.md`](references/privacy.md) 已禁止這種用法；SKILL 第 0 步要能明確停下來，而不是繼續寫報告。
- [ ] **離職與刪除權。** git 歷史刪不掉。導入 checklist 要寫保存多久、誰能 clone、離職時報告目錄怎麼處理。這不是程式能獨力解決的，但文件要當必做項。

---

## 歡迎這樣開始

| 你能做的 | 怎麼交 |
| :-- | :-- |
| 你日常用 Cursor / Gemini CLI / 公司內部工具 | `[collector]` PR，附實測數字 |
| 你的職能裡「用得好」在紀錄裡長得不一樣 | Issue 標題 `[判準] <職能>` |
| 報告把你做過的事判成沒做 | [誤判模板](.github/ISSUE_TEMPLATE/misjudgement.md) |
| 某型人物志的盲點／下一步不適用你的領域 | `[型錄]` PR |
| `3／5`、雷達圖、總覽英雄數字 | `[呈現]` PR |

不確定該做哪一條？開 Issue 標 `[roadmap]`，說你打算碰哪一項。已有人認領的，這份檔案會把 checkbox 打勾或連到 PR。

---

## 不會做

見 [CONTRIBUTING.md 的「不接受的貢獻」](CONTRIBUTING.md#不接受的貢獻)。排名、百分位、遠端集中掃描、自動上傳、把分型寫成有高低，都不是「還沒排程」，是這個專案存在的前提。

維護者私人 LifeOS（例如信箱助理的報價閘門）不在本 repo，請不要開相關 Issue。

---

## 技術備註

- 語言：Python 3.9+ 標準庫，沒有套件依賴
- 收集：`python3 scripts/collect.py --days 7 --no-content --out /tmp/check`
- 發布腳本語法：`bash -n scripts/publish.sh`
- Demo：`docs/` → https://ai.lifehacker.tw/reports/ai-level-check-demo/
- 本機生圖草稿在 `_local/`，不上傳 GitHub

## 關聯文件

- [`CONTRIBUTING.md`](CONTRIBUTING.md)：怎麼交、什麼不收
- [`references/log-sources.md`](references/log-sources.md)：各家紀錄格式
- [`references/privacy.md`](references/privacy.md)：紅線與面試／導入
- [`CHANGELOG.md`](CHANGELOG.md)：已發布的變更
