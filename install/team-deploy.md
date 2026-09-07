# 團隊部署

> **先讀 [references/privacy.md](../references/privacy.md)，再往下看。**
>
> 這套工具讀的是員工每天工作時打的字。技術上它做得到監控，
> 擋住它的只有制度，不是程式。沒有先跟團隊講清楚就裝，它就是監控軟體。

---

## 部署前：四件事先寫下來

發給團隊，白紙黑字，不要口頭說說：

1. **會讀什麼**：AI 對話紀錄。不含私人檔案、瀏覽紀錄、鍵盤側錄。
2. **誰能看**：報告的可見範圍。是主管、HR，還是只有本人。
3. **拿來做什麼**：明說「不作為考績單一依據」，並說明實際會怎麼用。
4. **不做什麼**：不排名、不自動決策、不跨人比較。

沒有這四件事的部署，本專案不建議進行。

---

## 架構

```
每個人的電腦                        團隊 private repo
┌──────────────────┐              ┌────────────────────────┐
│ ~/.claude/       │              │ reports/               │
│ ~/.codex/        │  collect.py  │   alice/2026-W36.html  │
│      │           │ ───────────► │   bob/2026-W36.html    │
│      ▼           │              │   carol/2026-W36.html  │
│  evidence/       │              │                        │
│  （不進版控）     │  AI 分析      │  git 歷史 = 存證        │
│      │           │ ───────────► │  推上去就改不掉         │
│      ▼           │  publish.sh  │                        │
│  reports/*.html  │              └────────────────────────┘
└──────────────────┘
     本人執行                          本人決定推不推
```

三個刻意的設計：

- **原始紀錄不離開本機。** `evidence/` 在 `.gitignore` 裡，推上去的只有報告。
- **每個人自己跑、自己推。** 沒有中央掃描，主管拿不到別人的原始對話。
- **推上去就刪不掉。** 這是它有公信力的來源——報告不能事後修飾。

---

## 一、建 private repo

```bash
gh repo create your-org/ai-level-log --private
```

建議的 repo 結構：

```
ai-level-log/
├── README.md          # 這一輪的規則、期間、誰要交
├── reports/
│   ├── alice/
│   ├── bob/
│   └── carol/
└── .github/
    └── CODEOWNERS     # 誰能 review
```

建議在 GitHub 開啟分支保護：禁止 force push、禁止刪除分支。
`publish.sh` 本身也不會做這兩件事，但擋在服務端更保險。

---

## 二、裝到每台電腦

### macOS / Linux

```bash
git clone https://github.com/Raymondhou0917/ai-level-check.git ~/ai-level-check
ln -s ~/ai-level-check ~/.claude/skills/ai-level-check
ln -s ~/ai-level-check ~/.codex/skills/ai-level-check    # 有裝 Codex 才需要
```

用 MDM 或 setup script 派送時，把上面三行放進去就好。
**不要**同時派送任何自動執行或自動上傳的排程——那會越過「本人決定」這一關。

### 設定顯示名稱

```bash
echo 'export AI_LEVEL_NAME="alice"' >> ~/.zshrc
```

`publish.sh` 用這個名字決定報告放在 `reports/<name>/` 底下。
沒設定的話會用系統帳號名。

---

## 三、每一期怎麼跑

建議雙週或每月一次。每個人在自己的電腦上：

```bash
cd ~/ai-level-check

# 1. 產證據包
python3 scripts/collect.py --days 14

# 2. 請 AI 產報告（在 Claude Code / Codex 裡）
#    「跑 ai-level-check，用 evidence/ 底下最新那份證據包」

# 3. 自己看過報告

# 4. 推
./scripts/publish.sh --period 2026-W36 --repo git@github.com:your-org/ai-level-log.git
```

第 3 步不能省。推上去改不掉，所以要推的那一版必須是本人看過的。

### 敏感期間

手上有還沒公開的專案、客戶資料特別敏感的期間，跑：

```bash
python3 scripts/collect.py --days 14 --no-content
```

報告只會有計數與行為描述，不含任何原文摘錄。

---

## 四、團隊層級怎麼看

**可以看的**：

- 分型分布。全隊都偏 `A`（不查核）比任何一個人的等級都值得處理。
- 共同的改善事項。三個人的報告都指出同一個缺口，那是流程問題不是個人問題。
- 制度化潛力。誰做出了值得全隊複用的東西。

**不要做的**：

- 把等級排成表格比較
- 把弱點列進面談紀錄
- 把報告接進任何自動化的人事流程

做了這三件事，下一期開始所有人都會為報告表演，這份紀錄就沒有參考價值了。

---

## 五、離職與保存

- 人離職時移除他的報告目錄。git 歷史刪不掉，所以更該在一開始就決定哪些東西不進去。
- 建議保存期限不超過兩年。
- repo 的存取權限跟著人事異動走，記得定期稽核。

---

## 常見問題

**Q：可以做成排程自動跑自動推嗎？**

技術上可以，但這會越過「本人看過才推」那一關，本專案不建議。
要降低摩擦的話，做成排程「產出報告並提醒本人」，推送仍然手動。

**Q：可以掃遠端伺服器上的紀錄嗎？**

`collect.py` 只讀本機路徑。要掃遠端等於在做集中監控，
請先確認法遵與勞動法規，那已經超出這個專案的設計範圍。

**Q：員工不想跑怎麼辦？**

那就不要跑。自願制是這套機制唯一能長期運作的前提。
強制執行會得到一堆為了好看而做的紀錄，比沒有更糟。
