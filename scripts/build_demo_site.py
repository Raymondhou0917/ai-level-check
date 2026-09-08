#!/usr/bin/env python3
"""Generate fictional LV1 / LV3 / LV4 demo reports under docs/.

These are dummy people and dummy work. Do not copy Raymond's real report.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

LADDER = [
    ("LV0", "拿到答案就用，沒先想過對不對"),
    ("LV1", "覺得不對就再問一次，換個說法繼續"),
    ("LV2", "某一類工作已經能穩定交給 AI 做完"),
    ("LV3", "交代得清楚；答錯時指得出哪裡不對"),
    ("LV4", "把有效做法做成別人也能用的模板或自動流程"),
    ("LV5", "整套工作會自己跑；例外有人接或會停；結果寫回做法"),
]


def ladder_html(on, part=None):
    rows = []
    for code, text in LADDER:
        cls = ""
        if code == on:
            cls = ' class="on"'
        elif code == part:
            cls = ' class="part"'
        rows.append(f"<li{cls}><b>{code}</b><span>{text}</span></li>")
    return "<ol class=\"ladder\">\n  " + "\n  ".join(rows) + "\n</ol>"


CANON_BASE = "https://ai.lifehacker.tw/reports/ai-level-check-demo"


def toc_html(current):
    items = [
        ("index.html", "⌂", "入口"),
        ("lv1.html", "1", "Demo 1 · LV1"),
        ("lv3.html", "2", "Demo 2 · LV3"),
        ("lv4.html", "3", "Demo 3 · LV4"),
    ]
    demos = []
    for href, n, label in items:
        cls = ' class="demo current"' if href == current else ' class="demo"'
        demos.append(f'<a{cls} href="{href}"><span class="tn">{n}</span>{label}</a>')
    chapters = [
        ("#s0", "00", "一看就懂"),
        ("#s1", "01", "工作怎麼用"),
        ("#s2", "02", "下一步"),
        ("#s3", "03", "能力細項"),
        ("#s4", "04", "工作系統"),
        ("#s5", "05", "值得留下"),
        ("#s6", "06", "結論"),
    ]
    ch = "\n  ".join(
        f'<a href="{href}"><span class="tn">{n}</span>{label}</a>'
        for href, n, label in chapters
    )
    return f"""<nav class="toc" id="toc" aria-label="示範與章節目錄">
  <div class="t">示範切換</div>
  {chr(10).join("  " + d for d in demos)}
  <div class="t">章節</div>
  {ch}
</nav>"""


def habitat(boxes, caption):
    """boxes: list of (x, name, sub, solid:bool). Shared rules box at bottom if any solid>1 or flag."""
    parts = [
        '<figure class="viz">',
        '  <svg class="diag" viewBox="0 0 800 260" role="img">',
        '    <defs>',
        '      <marker id="a" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
        '        <polygon points="0 0, 8 3, 0 6" fill="#4a4a4f"/>',
        '      </marker>',
        '    </defs>',
        '    <text x="40" y="28" fill="#77777d" font-size="12" font-family="Noto Sans TC, PingFang TC, sans-serif" letter-spacing="0.12em">這次有讀到的入口</text>',
    ]
    n = len(boxes)
    width = 144
    gap = (800 - 80 - n * width) / max(n - 1, 1) if n > 1 else 0
    xs = []
    for i, (name, sub, solid) in enumerate(boxes):
        x = 40 + i * (width + gap)
        xs.append(x + width / 2)
        stroke = "#2f5d62" if solid else "#c8c4bc"
        dash = "" if solid else ' stroke-dasharray="4,3"'
        sw = "1.2" if solid else "1"
        fill_ink = "#1c1c1e" if solid else "#4a4a4f"
        parts.append(
            f'    <rect x="{x:.0f}" y="44" width="{width}" height="64" rx="6" fill="#fdfcfa" stroke="{stroke}" stroke-width="{sw}"{dash}/>'
        )
        parts.append(
            f'    <text x="{x + width/2:.0f}" y="72" text-anchor="middle" fill="{fill_ink}" font-size="16" font-weight="600" font-family="Noto Serif TC, Songti TC, serif">{name}</text>'
        )
        parts.append(
            f'    <text x="{x + width/2:.0f}" y="92" text-anchor="middle" fill="#4a4a4f" font-size="12" font-family="Noto Sans TC, PingFang TC, sans-serif">{sub}</text>'
        )
        dash_line = "" if solid else ' stroke-dasharray="4,3"'
        parts.append(
            f'    <path d="M {x + width/2:.0f},108 V 156 H 400 V 176" fill="none" stroke="#4a4a4f" stroke-width="1.2"{dash_line} marker-end="url(#a)"/>'
        )
    parts.append(
        '    <rect x="248" y="176" width="304" height="56" rx="6" fill="rgba(47,93,98,0.08)" stroke="#2f5d62" stroke-width="1.4"/>'
    )
    parts.append(
        '    <text x="400" y="200" text-anchor="middle" fill="#1c1c1e" font-size="15" font-weight="600" font-family="Noto Serif TC, Songti TC, serif">工作規則</text>'
    )
    parts.append(
        '    <text x="400" y="218" text-anchor="middle" fill="#4a4a4f" font-size="12" font-family="Noto Sans TC, PingFang TC, sans-serif">見各示範頁說明</text>'
    )
    parts.append("  </svg>")
    parts.append(f"  <figcaption>{caption}</figcaption>")
    parts.append("</figure>")
    return "\n".join(parts)


def gears(states):
    """states: 5 tuples (on:bool, title, note)"""
    cells = []
    for on, title, note in states:
        cls = ' class="gear on"' if on else ' class="gear"'
        st = "有看到" if on else "這段沒看到"
        cells.append(
            f"""  <div{cls}>
    <p class="st">{st}</p>
    <h4>{title}</h4>
    <p>{note}</p>
  </div>"""
        )
    return '<div class="gear-row">\n' + "\n".join(cells) + "\n</div>"


def checks(items):
    cells = []
    for on, st, title in items:
        cls = ' class="check on"' if on else ' class="check"'
        cells.append(
            f"""  <div{cls}>
    <p class="st">{st}</p>
    <h4>{title}</h4>
  </div>"""
        )
    return '<div class="check-row">\n' + "\n".join(cells) + "\n</div>"


def page(filename, title, description, body):
    canon = f"{CANON_BASE}/{filename}"
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">
<meta name="ai-content-signal" content="search=yes, ai-input=yes, ai-train=yes">
<meta name="description" content="{description}">
<title>{title}</title>
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="zh_TW">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{CANON_BASE}/screenshots/01-overview.jpg">
<link rel="stylesheet" href="assets/report.css">
</head>
<body>
<button class="toc-btn" id="toc-btn" type="button">☰ 章節目錄</button>
{toc_html(filename)}
<div class="wrap">
{body}
<footer class="site-footer">
  <p>
    這是開源專案
    <a href="https://github.com/Raymondhou0917/ai-level-check">ai-level-check</a>
    的<strong>虛構示範</strong>，不是真實紀錄。
  </p>
  <p>
    方法見
    <a href="https://ai.lifehacker.tw/">AI Agent 學習站</a>。
    這是觀察紀錄的版型示範，不能當作考績、升遷或人事決定的依據，也不提供排名。
  </p>
</footer>
</div>
<script src="assets/demo.js"></script>
</body>
</html>
"""


BANNER = """<p class="demo-banner">
  <b>虛構示範。</b>這三份是假資料，用來對照 LV1、LV3、LV4。目錄可切 Demo。
</p>"""


BODY_LV1 = f"""
<header id="s0">
  <h1>AI 使用能力報告</h1>
  <p class="meta">示範・林可安（虛構）　·　看的是 2026-08-26 到 09-08 這 14 天，網頁對話貼上來的內容　·　2026-09-08 產出</p>
</header>
{BANNER}
<p class="lede">
這份報告在回答一件事：這個人平常怎麼跟 AI 一起做事、已經能獨立完成什麼、下一次該補哪一件。
不是考試排名，也不是「會不會寫提示詞」的分數。
</p>
<p class="scope">
讀的是本人貼上來的 ChatGPT 網頁對話，不是本機硬碟上的工作紀錄。
這 14 天共 22 則對話、61 則訊息，全部是本人打字。沒有工具呼叫、沒有排程、沒有草稿信箱。
沒讀到的來源：任何本機 agent、會議、通訊軟體上口頭交代的工作。
所以這份報告描述的是「貼進來的問答」，不是這個人全部的工作。貼上模式通常最多穩到第 3 級。
</p>
<div class="verdict">
  <span class="lv">LV1</span>
  <span class="name">換句話重問：覺得不對就再問一次，還沒把完成標準一次講清楚</span>
  <p class="gap">
    白話：他會察覺「這句不像我要的」，然後換個形容詞再請它寫。
    還看不到「第一次就把怎樣算完成講清楚」，也還沒看到做完去核對。
    這 14 天讀到的用法，停在這裡。
  </p>
</div>
<div class="glance">
  <section>
    <h3>擅長什麼</h3>
    <ul>
      <li>願意一直問，不會拿到第一版就交差（案例 1、2）</li>
      <li>用在活動頁標題和週報開頭（案例 1、4）</li>
    </ul>
  </section>
  <section>
    <h3>目前沒做好</h3>
    <ul>
      <li>不滿意時只說「再幽默一點」「再短一點」，指不出哪一句不行</li>
      <li>產出沒拿去對現場資料，直接準備貼</li>
    </ul>
  </section>
  <section>
    <h3>下一步</h3>
    <p class="do">
      同一則活動頁，第一句就寫：給誰看、不能寫什麼、怎樣算能上架。
    </p>
  </section>
</div>
{ladder_html("LV1")}
<h3>這一級為什麼算過、還要注意什麼</h3>
<p>
<strong>為什麼是第 1 級：</strong>22 則裡有 14 則是「再寫一次／換個語氣」（案例 1、2）。
他知道第一版不對，推進方式是換說法，不是補條件。
</p>
<p>
<strong>還沒看到、所以不往上寫：</strong>沒有一則第一次交辦就帶完成標準；沒有打開檔案或瀏覽器去核對。
本機也掃不到紀錄，不能因此說他不會用 agent，只能說這份材料看不到。
</p>
<div class="persona">
  <div class="code">QAOC</div>
  <p><strong>閒聊夥伴</strong>　先丟一句話，產出直接用，做完不留下模板，也還沒讓 AI 改檔案。</p>
  <div class="bento-axes">
    <article>
      <p class="k">交辦 · Q</p>
      <h4>先問再說</h4>
      <p>案例 1 第一句是「幫我寫十個活動標題」。</p>
    </article>
    <article>
      <p class="k">查核 · A</p>
      <h4>直接採用或再問</h4>
      <p>沒有「這數字哪來的」或對現場資料。不滿意就再生成。</p>
    </article>
    <article>
      <p class="k">沉澱 · O</p>
      <h4>一次性</h4>
      <p>每次從空白對話開始，沒有可重用說明。</p>
    </article>
    <article>
      <p class="k">動手 · C</p>
      <h4>只對話</h4>
      <p>網頁聊天。沒有改檔、沒有瀏覽器檢查。</p>
    </article>
  </div>
  <p class="disclaimer">這是使用習慣的分類，不是能力高低，也不能拿來跟別人比。</p>
</div>

<h2 id="s1">一、這 14 天，AI 實際被用在哪</h2>
<figure>
  <ul class="bars">
    <li><span>本人親自操作</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">22</span></li>
    <li><span>系統自己在跑</span><span class="track"><span class="fill dim" style="width:0%"></span></span><span class="v">0</span></li>
    <li><span>被派出的小幫手</span><span class="track"><span class="fill dim" style="width:0%"></span></span><span class="v">0</span></li>
  </ul>
  <figcaption>圖 1：全部是本人打字。沒有自動化，所以下面兩排是 0。這在貼上模式很常見。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>本人打出去的訊息</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">61</span></li>
    <li><span>平均一則對話幾則</span><span class="track"><span class="fill dim" style="width:28%"></span></span><span class="v">2.8</span></li>
  </ul>
  <p class="note">最好的 AI 工作者是用最少的訊息數跟最少的 token 達到一樣的成果；但因為每個人對工作成果好的標準不同，這個數字無法直接拿來評估，僅供參考。</p>
  <figcaption>圖 1b：22 則對話、61 則訊息。來回多，多半是換個說法再要一版。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>用 ChatGPT 網頁親自做</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">22</span></li>
  </ul>
  <figcaption>圖 2：只讀到一個入口。則數多寡不是能力。</figcaption>
</figure>
<div class="scroll wide">
<table>
<thead><tr>
  <th>看什麼</th><th>實際看到的做法</th><th>依據</th>
  <th>是偶爾還是習慣</th><th>沒做好的地方</th><th>這個判斷有多有把握</th>
</tr></thead>
<tbody>
  <tr>
    <td>平常拿 AI 做什麼</td>
    <td>活動頁標題、週報開頭、會議紀錄翻譯</td>
    <td>案例 1–4</td>
    <td>這 14 天有紀錄</td>
    <td>產出沒對現場資料</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>交代與核對</td>
    <td>先丟一句話；不滿意再補形容詞</td>
    <td>案例 1、2</td>
    <td>習慣</td>
    <td>沒有完成標準、沒有核對</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>發現不對時怎麼改</td>
    <td>「再幽默一點」「再短一點」</td>
    <td>案例 1、2</td>
    <td>多次</td>
    <td>指不出哪一句不行</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>有沒有留下可交接的東西</td>
    <td>沒有</td>
    <td>—</td>
    <td>—</td>
    <td>每次從空白開始</td>
    <td><span class="tag high">高</span></td>
  </tr>
</tbody>
</table>
</div>
<details class="cases" id="cases">
  <summary>點這裡看：表格裡的「案例」實際是哪一件工作</summary>
  <p class="note">以下是虛構示範。真實報告會放這段期間電腦裡留下的對話標題。</p>
  <div class="scroll">
  <table class="case-table">
    <thead><tr><th class="n">#</th><th>這件工作</th><th>誰在做</th><th>入口</th><th>日期</th></tr></thead>
    <tbody>
      <tr><td colspan="5" class="g">本人親自操作</td></tr>
      <tr><td class="n">1</td><td>請它寫十個社群活動標題</td><td class="who">本人</td><td class="src">ChatGPT 網頁</td><td class="dt">08-27</td></tr>
      <tr><td class="n">2</td><td>覺得不夠幽默，再說一次「再活一點」</td><td class="who">本人</td><td class="src">ChatGPT 網頁</td><td class="dt">08-27</td></tr>
      <tr><td class="n">3</td><td>把會議紀錄翻成對外短訊</td><td class="who">本人</td><td class="src">ChatGPT 網頁</td><td class="dt">09-02</td></tr>
      <tr><td class="n">4</td><td>請它幫想週報開頭兩段</td><td class="who">本人</td><td class="src">ChatGPT 網頁</td><td class="dt">09-06</td></tr>
    </tbody>
  </table>
  </div>
</details>

<h2 id="s2">二、下一步：先補哪一件</h2>
<h3>1. 同一件事，開頭寫死完成標準　<span class="tag warn">本週只做這件</span></h3>
<ul>
  <li><strong>看到什麼：</strong>不滿意時換形容詞，AI 只能猜。</li>
  <li><strong>下次怎麼做：</strong>活動頁第一則訊息寫：給誰看、不能出現什麼詞、幾字以內、怎樣算能上架。</li>
  <li><strong>怎樣算完成：</strong>連續兩則真實工作，第一句就帶這三行，不必再「再寫一次」當主路徑。</li>
</ul>
<p>不必為此去裝 Claude Code。先把網頁對話的第一句講清楚，等級才有材料往上走。</p>

<h2 id="s3">三、能力細項</h2>
<div class="scroll wide">
<table>
<thead><tr><th>看哪一項</th><th>目前程度</th><th>依據</th><th>做得好的地方</th><th>要改的地方</th></tr></thead>
<tbody>
  <tr><td>把工作講清楚、拆開做</td><td>偶爾</td><td>案例 1</td><td>願意多問</td><td>第一句沒帶完成標準</td></tr>
  <tr><td>來回修正</td><td>有在做</td><td>案例 2</td><td>不會第一版就停</td><td>修正方式是換形容詞</td></tr>
  <tr><td>做完有沒有核對</td><td>沒看到</td><td>—</td><td>—</td><td>產出沒對現場</td></tr>
  <tr><td>會不會讓 AI 真的動手</td><td>只對話</td><td>全部</td><td>適合文案場景</td><td>不是弱點，是入口限制</td></tr>
  <tr><td>有沒有把做法留給下次</td><td>沒看到</td><td>—</td><td>—</td><td>每次從空白開始</td></tr>
</tbody>
</table>
</div>

<h2 id="s4">四、工作系統長什麼樣子</h2>
<h3>換一家 AI，能不能接著做</h3>
<p>這次只讀到 ChatGPT 網頁。沒有共用規則檔，換一個視窗就要把背景再說一次。</p>
{habitat(
    [("ChatGPT", "本人 22 則", True), ("本機 agent", "這次沒讀到", False)],
    "圖 3：目前是單一口徑的聊天視窗。虛線不是他不會，是這份材料沒有。",
)}
{gears([
    (False, "時間到就動", "貼上模式看不到排程。"),
    (False, "外面一推就動", "沒有表單或留言接收端。"),
    (False, "進出關卡", "沒有。"),
    (False, "推上去就上線", "沒有。"),
    (False, "倒下拉起來", "沒有。"),
])}
<p class="note">沒看到只代表這 14 天這份材料沒有。覆蓋度不是分數。文案工作本來就不需要五顆齒輪。</p>
<h3>四項系統檢查</h3>
{checks([
    (False, "不適用", "只看文件做得完嗎"),
    (False, "不適用", "資料不齊會停嗎"),
    (False, "沒有系統可測", "沒人盯著還在跑"),
    (False, "尚未觀察", "出事找得到人"),
])}

<h2 id="s5">五、值得留下的做法</h2>
<div class="scroll">
<table>
<thead><tr><th>做法</th><th>現在怎麼用</th><th>以後可以怎麼用</th><th>下一步</th></tr></thead>
<tbody>
  <tr>
    <td>不滿意就再問，不把第一版當定稿</td>
    <td>已經在用</td><td>把「再問」改成「指出哪一句不行」</td><td>見下一節那三行完成標準</td>
  </tr>
</tbody>
</table>
</div>

<h2 id="s6">六、給本人與主管的結論</h2>
<ol>
  <li><strong>現在的位置：</strong>會用、會再問，用法停在換句話重問。這一級過了。</li>
  <li><strong>下週只做一件事：</strong>真實的一則活動頁，第一句寫死給誰看、不能寫什麼、怎樣算能上架。</li>
  <li><strong>別為了這份報告去裝工具。</strong>先把第一句講清楚。</li>
</ol>
"""


BODY_LV3 = f"""
<header id="s0">
  <h1>AI 使用能力報告</h1>
  <p class="meta">示範・周子寧（虛構）　·　看的是 2026-08-26 到 09-08 這 14 天，電腦裡實際留下的工作紀錄　·　2026-09-08 產出</p>
</header>
{BANNER}
<p class="lede">
這份報告在回答一件事：這個人平常怎麼跟 AI 一起做事、已經能獨立完成什麼、下一次該補哪一件。
不是考試排名，也不是「會不會寫提示詞」的分數。
</p>
<p class="scope">
讀的是這台電腦上 Claude Code 的對話紀錄。
這 14 天共 41 則對話；本人親自打字的有 41 則（186 則訊息），其中 28 則有實際改檔或開瀏覽器。
沒有排程、沒有系統在無人時自己跑。沒讀到的來源：ChatGPT 網頁、會議、口頭交代。
所以這份報告描述的是「在這一個入口裡實際發生的事」，不是這個人全部的工作。
</p>
<div class="verdict">
  <span class="lv">LV3</span>
  <span class="name">精準下指令：交代得清楚，答錯時指得出哪裡不對，做完會去看</span>
  <p class="gap">
    白話：第一次就講背景與完成標準，色票不對會指出哪三個 token，改完自己打開頁面看。
    還沒看到他把這套改稿流程寫成下次能直接跑的說明。所以停在第 3 級，不是第 4 級。
  </p>
</div>
<div class="glance">
  <section>
    <h3>擅長什麼</h3>
    <ul>
      <li>第一次交代就帶完成標準（案例 1、4）</li>
      <li>答錯時指得出具體哪裡不對，不是只說重寫（案例 2）</li>
      <li>做完會打開頁面核對，不是看了就信（案例 1、3）</li>
    </ul>
  </section>
  <section>
    <h3>目前沒做好</h3>
    <ul>
      <li>同一套改作品集的流程，下一則對話又從頭講一遍</li>
      <li>只有一個入口有本人操作；規則沒寫成共用檔</li>
    </ul>
  </section>
  <section>
    <h3>下一步</h3>
    <p class="do">
      把「改作品集頁」這次真的走通的步驟寫進一份 SKILL.md，下一則同類工作只補這次不一樣的地方。
    </p>
  </section>
</div>
{ladder_html("LV3")}
<h3>這一級為什麼算過、還要注意什麼</h3>
<p>
<strong>為什麼是第 3 級：</strong>案例 1 第一句就寫給誰看、哪些區塊能動、怎樣算能合併；
案例 2 不說「重寫」，而是列出三個色票 token；案例 3 改完自己開瀏覽器看。
這是精準下指令加上查核，不是單點碰運氣。
</p>
<p>
<strong>為什麼還不是第 4 級：</strong>沒有可重用說明、沒有模板、沒有排程。
有效做法還停在他腦子裡與單則對話裡。未觀察到不等於不會，只是這 14 天沒讀到。
</p>
<div class="persona">
  <div class="code">PVOE</div>
  <p><strong>精準特工</strong>　交辦清楚、會驗證、會讓 AI 動手改檔，做完當這次的事結束。</p>
  <div class="bento-axes">
    <article>
      <p class="k">交辦 · P</p>
      <h4>先講清楚再做</h4>
      <p>案例 1、4 第一次就帶背景與完成標準。</p>
    </article>
    <article>
      <p class="k">查核 · V</p>
      <h4>動手核對</h4>
      <p>案例 3 開瀏覽器對頁面；這段期間 19 次測試或比對。</p>
    </article>
    <article>
      <p class="k">沉澱 · O</p>
      <h4>一次性</h4>
      <p>沒有寫進 SKILL 或模板。下一則同類工作又從頭講。</p>
    </article>
    <article>
      <p class="k">動手 · E</p>
      <h4>讓 AI 直接動手</h4>
      <p>改檔、跑測試、開頁面，不是只聊天。</p>
    </article>
  </div>
  <p class="disclaimer">這是使用習慣的分類，不是能力高低，也不能拿來跟別人比。</p>
</div>

<h2 id="s1">一、這 14 天，AI 實際被用在哪</h2>
<figure>
  <ul class="bars">
    <li><span>本人親自操作</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">41</span></li>
    <li><span>系統自己在跑</span><span class="track"><span class="fill dim" style="width:0%"></span></span><span class="v">0</span></li>
    <li><span>被派出的小幫手</span><span class="track"><span class="fill dim" style="width:0%"></span></span><span class="v">0</span></li>
  </ul>
  <figcaption>圖 1：全部是本人坐在前面做。沒有自動化，不是壞事——這個人的工作還不需要系統自己跑。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>本人打出去的訊息</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">186</span></li>
    <li><span>平均一則對話幾則</span><span class="track"><span class="fill dim" style="width:45%"></span></span><span class="v">4.5</span></li>
  </ul>
  <p class="note">最好的 AI 工作者是用最少的訊息數跟最少的 token 達到一樣的成果；但因為每個人對工作成果好的標準不同，這個數字無法直接拿來評估，僅供參考。</p>
  <figcaption>圖 1b：41 則對話、186 則訊息。來回是在對規格，不是在換形容詞。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>用 Claude 親自做</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">41</span></li>
  </ul>
  <figcaption>圖 2：本人打字出現在一個入口。則數多寡不是能力。</figcaption>
</figure>
<div class="scroll wide">
<table>
<thead><tr>
  <th>看什麼</th><th>實際看到的做法</th><th>依據</th>
  <th>是偶爾還是習慣</th><th>沒做好的地方</th><th>這個判斷有多有把握</th>
</tr></thead>
<tbody>
  <tr>
    <td>平常拿 AI 做什麼</td>
    <td>直接改作品集頁、客戶 FAQ、活動頁文案</td>
    <td>案例 1–4</td>
    <td>習慣</td>
    <td>無</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>交代與核對</td>
    <td>第一次就講背景與完成標準；做完開頁面看</td>
    <td>案例 1、3</td>
    <td>習慣</td>
    <td>無</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>發現不對時怎麼改</td>
    <td>列出三個色票 token，不說「重寫」</td>
    <td>案例 2</td>
    <td>多次</td>
    <td>無</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>有沒有留下可交接的東西</td>
    <td>沒有寫進可重用位置</td>
    <td>—</td>
    <td>—</td>
    <td>下一則又從頭講</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>換一家 AI 能不能接著做</td>
    <td>這次只讀到一個入口</td>
    <td>—</td>
    <td>—</td>
    <td>尚未觀察，不擋第 3 級</td>
    <td><span class="tag warn">中</span></td>
  </tr>
</tbody>
</table>
</div>
<details class="cases" id="cases">
  <summary>點這裡看：表格裡的「案例」實際是哪一件工作</summary>
  <p class="note">以下是虛構示範。</p>
  <div class="scroll">
  <table class="case-table">
    <thead><tr><th class="n">#</th><th>這件工作</th><th>誰在做</th><th>入口</th><th>日期</th></tr></thead>
    <tbody>
      <tr><td colspan="5" class="g">本人親自操作</td></tr>
      <tr><td class="n">1</td><td>改作品集首頁，第一句就寫哪些區塊能動、怎樣算能合併</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">08-28</td></tr>
      <tr><td class="n">2</td><td>色票不對，列出三個 token 名稱請它改，不要重寫整頁</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">08-28</td></tr>
      <tr><td class="n">3</td><td>改完自己開本機頁面對一次間距</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">08-29</td></tr>
      <tr><td class="n">4</td><td>把客戶 FAQ 長文改短，並寫死不能出現的語氣</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">09-04</td></tr>
    </tbody>
  </table>
  </div>
</details>

<h2 id="s2">二、下一步：先補哪一件</h2>
<h3>1. 把已走通的改稿流程寫下來　<span class="tag warn">本週只做這件</span></h3>
<ul>
  <li><strong>看到什麼：</strong>作品集改稿已經能穩定做完，但下一則對話又把完成標準講一次。</li>
  <li><strong>下次怎麼做：</strong>從案例 1–3 抽出步驟，寫成一份 SKILL.md，放在專案裡。</li>
  <li><strong>怎樣算完成：</strong>下一則同類工作，第一句只補「這次不一樣的地方」，不再貼完整規格。</li>
</ul>
<p>不必為此去接第二個 AI 入口，也不必排程。第 4 級先看有沒有留下別人也能用的做法。</p>

<h2 id="s3">三、能力細項</h2>
<div class="scroll wide">
<table>
<thead><tr><th>看哪一項</th><th>目前程度</th><th>依據</th><th>做得好的地方</th><th>要改的地方</th></tr></thead>
<tbody>
  <tr><td>把工作講清楚、拆開做</td><td>穩定在用</td><td>案例 1、4</td><td>第一次交代就含範圍與完成標準</td><td>見下一節，寫下來</td></tr>
  <tr><td>來回修正</td><td>穩定在用</td><td>案例 2</td><td>逐條規格，不是只說不對</td><td>—</td></tr>
  <tr><td>做完有沒有核對</td><td>穩定在用</td><td>案例 3</td><td>開頁面對間距</td><td>—</td></tr>
  <tr><td>會不會讓 AI 真的動手</td><td>穩定在用</td><td>案例 1–3</td><td>改檔、測試、瀏覽器</td><td>—</td></tr>
  <tr><td>有沒有把做法留給下次</td><td>沒看到</td><td>—</td><td>—</td><td>寫進 SKILL</td></tr>
</tbody>
</table>
</div>

<h2 id="s4">四、工作系統長什麼樣子</h2>
<h3>換一家 AI，能不能接著做</h3>
<p>這次只讀到 Claude。沒有第二個入口的本人操作，也還沒有一份兩邊都讀得到的規則。這不擋第 3 級。</p>
{habitat(
    [("Claude", "本人 41 則", True), ("其他入口", "這次沒讀到", False)],
    "圖 3：單一口徑、做法還在對話裡。要到第 5 級才需要兩個入口讀同一份規則。",
)}
{gears([
    (False, "時間到就動", "沒有排程。現在也不需要。"),
    (False, "外面一推就動", "沒有。"),
    (False, "進出關卡", "沒有。"),
    (False, "推上去就上線", "這 14 天沒看到實際呼叫。"),
    (False, "倒下拉起來", "沒有。"),
])}
<p class="note">沒看到只代表這 14 天沒動到。覆蓋度不是分數。獨立設計工作常常零顆齒輪也夠。</p>
<h3>四項系統檢查</h3>
{checks([
    (False, "還沒測", "只看文件做得完嗎"),
    (False, "還沒測", "資料不齊會停嗎"),
    (False, "沒有系統可測", "沒人盯著還在跑"),
    (False, "尚未觀察", "出事找得到人"),
])}
<p class="note">四項沒測不自動降級。現在也還沒有一套「系統」需要測。</p>

<h2 id="s5">五、值得留下的做法</h2>
<div class="scroll">
<table>
<thead><tr><th>做法</th><th>現在怎麼用</th><th>以後可以怎麼用</th><th>下一步</th></tr></thead>
<tbody>
  <tr>
    <td>色票不對就列 token 名稱，不說重寫整頁（案例 2）</td>
    <td>已經在用</td><td>寫進改稿 SKILL 的「修正時」一節</td><td>本週把這句搬進檔案</td>
  </tr>
  <tr>
    <td>改完自己開頁面對一次（案例 3）</td>
    <td>已經在用</td><td>當成完成標準最後一行</td><td>維持</td>
  </tr>
</tbody>
</table>
</div>

<h2 id="s6">六、給本人與主管的結論</h2>
<ol>
  <li><strong>現在的位置：</strong>能把一件真實工作交代清楚、改錯、核對完。這一級過了。</li>
  <li><strong>下週只做一件事：</strong>把作品集改稿步驟寫成一份 SKILL.md。不要同時去接第二個入口。</li>
  <li><strong>請留下的習慣：</strong>指出具體哪裡不對。這比任何工具名單都更接近下一級。</li>
</ol>
"""


BODY_LV4 = f"""
<header id="s0">
  <h1>AI 使用能力報告</h1>
  <p class="meta">示範・何柏廷（虛構）　·　看的是 2026-08-26 到 09-08 這 14 天，電腦裡實際留下的工作紀錄　·　2026-09-08 產出</p>
</header>
{BANNER}
<p class="lede">
這份報告在回答一件事：這個人平常怎麼跟 AI 一起做事、已經能獨立完成什麼、下一次該補哪一件。
不是考試排名，也不是「會不會寫提示詞」的分數。
</p>
<p class="scope">
讀的是這台電腦上 Claude 與 Codex 的對話紀錄。
這 14 天共 37 則對話；本人親自打字的有 29 則（112 則訊息），另有 8 則是他寫好的週報流程被排程叫醒。
沒讀到的來源：網頁版 Chat、會議、口頭交代。
所以這份報告描述的是「在這兩個入口裡實際發生的事」，不是這個人全部的工作。
</p>
<div class="verdict">
  <span class="lv">LV4</span>
  <span class="name">模組化使用：有效做法寫成可重用說明，啟用前有測過，系統還沒自己營運</span>
  <p class="gap">
    白話：週報改稿變成一份 skill，加上每天早上的排程草稿。
    本人還在場才叫得動大部分工作；例外發生時沒有固定的「先停、再找人」迴路。所以是第 4 級，還不是第 5 級。
  </p>
</div>
<div class="glance">
  <section>
    <h3>擅長什麼</h3>
    <ul>
      <li>把走通的週報流程寫成 SKILL.md，下一則只補差異（案例 1、2）</li>
      <li>啟用排程前有拿一週舊稿跑過（案例 2）</li>
      <li>Claude 寫、Codex 改，讀的是同一份說明（案例 1、3）</li>
    </ul>
  </section>
  <section>
    <h3>目前沒做好</h3>
    <ul>
      <li>排程只有 8 則，失敗時沒有固定找誰</li>
      <li>客戶 FAQ 模板還只在一個專案裡，第二個案子又手貼一次</li>
    </ul>
  </section>
  <section>
    <h3>下一步</h3>
    <p class="do">
      週報 skill 檔頭補四欄：維護人、版本、怎樣算能貼、出錯寫給誰。第三個入口這週不必接。
    </p>
  </section>
</div>
{ladder_html("LV4", part="LV5")}
<h3>這一級為什麼算過、還要注意什麼</h3>
<p>
<strong>為什麼是第 4 級：</strong>案例 1 把週報改稿寫成可重用說明；案例 2 排程啟用前用舊稿測過；
案例 3 在 Codex 接著改同一份說明，不是各抄一份。這是模組化使用。
</p>
<p>
<strong>為什麼還不是第 5 級：</strong>系統還不是「本人不在也持續營運」。8 則排程都在他還會看的時段；
沒有讀到例外停手、結果寫回做法的迴路。兩個入口有本人操作，但第 5 級要的是系統在跑加上例外有人接，不是「有 skill 就升」。
</p>
<div class="persona">
  <div class="code">PVSE</div>
  <p><strong>系統建築師</strong>　交辦前先想清楚，做完會留下一套別人也能跑的東西。分型不是分數，第 4 級也可以是這型。</p>
  <div class="bento-axes">
    <article>
      <p class="k">交辦 · P</p>
      <h4>先講清楚再做</h4>
      <p>案例 1、4 帶背景與完成標準。</p>
    </article>
    <article>
      <p class="k">查核 · V</p>
      <h4>動手核對</h4>
      <p>案例 2 用舊稿走一遍才打開排程。</p>
    </article>
    <article>
      <p class="k">沉澱 · S</p>
      <h4>留下可再用的東西</h4>
      <p>SKILL.md ＋ 排程。案例 1、2。</p>
    </article>
    <article>
      <p class="k">動手 · E</p>
      <h4>讓 AI 直接動手</h4>
      <p>改檔、跑排程，不是只聊天。</p>
    </article>
  </div>
  <p class="disclaimer">這是使用習慣的分類，不是能力高低，也不能拿來跟別人比。</p>
</div>

<h2 id="s1">一、這 14 天，AI 實際被用在哪</h2>
<figure>
  <ul class="bars">
    <li><span>本人親自操作</span><span class="track"><span class="fill" style="width:78%"></span></span><span class="v">29</span></li>
    <li><span>系統自己在跑</span><span class="track"><span class="fill dim" style="width:22%"></span></span><span class="v">8</span></li>
    <li><span>被派出的小幫手</span><span class="track"><span class="fill dim" style="width:0%"></span></span><span class="v">0</span></li>
  </ul>
  <figcaption>圖 1：已經有一點「做好的東西自己跑」，量還少，而且都在他還會看的時段。上面那排仍用來判斷他怎麼交代工作。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>本人打出去的訊息</span><span class="track"><span class="fill" style="width:100%"></span></span><span class="v">112</span></li>
    <li><span>平均一則對話幾則</span><span class="track"><span class="fill dim" style="width:39%"></span></span><span class="v">3.9</span></li>
  </ul>
  <p class="note">最好的 AI 工作者是用最少的訊息數跟最少的 token 達到一樣的成果；但因為每個人對工作成果好的標準不同，這個數字無法直接拿來評估，僅供參考。</p>
  <figcaption>圖 1b：29 則對話、112 則訊息。有 skill 之後，平均來回比從頭講規格時少。</figcaption>
</figure>
<figure>
  <ul class="bars">
    <li><span>用 Claude 親自做</span><span class="track"><span class="fill" style="width:69%"></span></span><span class="v">20</span></li>
    <li><span>用 Codex 親自做</span><span class="track"><span class="fill" style="width:31%"></span></span><span class="v">9</span></li>
  </ul>
  <figcaption>圖 2：本人打字出現在兩個入口。則數多寡不是能力。</figcaption>
</figure>
<div class="scroll wide">
<table>
<thead><tr>
  <th>看什麼</th><th>實際看到的做法</th><th>依據</th>
  <th>是偶爾還是習慣</th><th>沒做好的地方</th><th>這個判斷有多有把握</th>
</tr></thead>
<tbody>
  <tr>
    <td>平常拿 AI 做什麼</td>
    <td>內部週報、活動頁文案、客戶 FAQ</td>
    <td>案例 1–4</td>
    <td>習慣</td>
    <td>無</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>交代與核對</td>
    <td>第一次就講完成標準；排程啟用前用舊稿測</td>
    <td>案例 1、2</td>
    <td>習慣</td>
    <td>無</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>有沒有留下可交接的東西</td>
    <td>週報 SKILL.md；每天早上產出草稿</td>
    <td>案例 1、2</td>
    <td>習慣</td>
    <td>檔頭還沒寫出錯找誰</td>
    <td><span class="tag high">高</span></td>
  </tr>
  <tr>
    <td>換一家 AI 能不能接著做</td>
    <td>兩個入口有本人操作；說明指向同一份檔</td>
    <td>案例 1、3</td>
    <td>這 14 天有紀錄</td>
    <td>故障切換尚未觀察，不擋第 4 級</td>
    <td><span class="tag high">高</span></td>
  </tr>
</tbody>
</table>
</div>
<details class="cases" id="cases">
  <summary>點這裡看：表格裡的「案例」實際是哪一件工作</summary>
  <p class="note">以下是虛構示範。前 4 則本人坐在前面做；後 1 則排程叫醒。</p>
  <div class="scroll">
  <table class="case-table">
    <thead><tr><th class="n">#</th><th>這件工作</th><th>誰在做</th><th>入口</th><th>日期</th></tr></thead>
    <tbody>
      <tr><td colspan="5" class="g">本人親自操作</td></tr>
      <tr><td class="n">1</td><td>把週報改稿步驟寫成 SKILL.md，下一則只補這週不一樣的來源</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">08-27</td></tr>
      <tr><td class="n">2</td><td>用上一週舊稿跑一遍，確認格式能貼，才打開每天早上的排程</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">08-28</td></tr>
      <tr><td class="n">3</td><td>在 Codex 依同一份說明改活動頁語氣</td><td class="who">本人</td><td class="src">Codex</td><td class="dt">09-01</td></tr>
      <tr><td class="n">4</td><td>客戶 FAQ 做成模板，但第二個案子又手貼了一次</td><td class="who">本人</td><td class="src">Claude</td><td class="dt">09-05</td></tr>
      <tr><td colspan="5" class="g">排程叫醒</td></tr>
      <tr class="auto"><td class="n">5</td><td>每天早上產出週報草稿到指定資料夾</td><td class="who">系統</td><td class="src">自動</td><td class="dt">08-29 起</td></tr>
    </tbody>
  </table>
  </div>
</details>

<h2 id="s2">二、下一步：先補哪一件</h2>
<h3>1. 週報 skill 寫清「出錯找誰」　<span class="tag warn">本週只做這件</span></h3>
<ul>
  <li><strong>看到什麼：</strong>流程會跑，檔頭沒有維護人、版本、驗收、回報窗口。</li>
  <li><strong>為什麼要管：</strong>第 5 級要的不是更多排程，是例外發生時找得到人、結果會寫回做法。</li>
  <li><strong>下次怎麼做：</strong>檔頭加四欄。草稿不好就改那一週；規則要動再開新對話回寫 skill。</li>
  <li><strong>怎樣算完成：</strong>下一次週報格式跑掉時，對話裡找得到「先停、寫給誰、要不要改規則」。</li>
</ul>
<p>不必為了報告去接第三個入口，也不必演一場假故障。</p>

<h2 id="s3">三、能力細項</h2>
<div class="scroll wide">
<table>
<thead><tr><th>看哪一項</th><th>目前程度</th><th>依據</th><th>做得好的地方</th><th>要改的地方</th></tr></thead>
<tbody>
  <tr><td>把工作講清楚、拆開做</td><td>穩定在用</td><td>案例 1、4</td><td>有 skill 之後第一句只補差異</td><td>—</td></tr>
  <tr><td>做完有沒有核對</td><td>穩定在用</td><td>案例 2</td><td>啟用前用舊稿測</td><td>—</td></tr>
  <tr><td>會不會讓 AI 真的動手</td><td>穩定在用</td><td>案例 1–3</td><td>改檔與排程</td><td>—</td></tr>
  <tr><td>有沒有把做法留給下次</td><td>穩定在用</td><td>案例 1、2</td><td>SKILL ＋ 排程</td><td>檔頭補四欄</td></tr>
</tbody>
</table>
</div>

<h2 id="s4">四、工作系統長什麼樣子</h2>
<h3>換一家 AI，能不能接著做</h3>
<p>兩個入口有本人操作，說明指向同一份檔。這對第 4 級夠了。故障當天立刻切，這 14 天還沒碰到。</p>
{habitat(
    [("Claude", "本人 20 則", True), ("Codex", "本人 9 則", True)],
    "圖 3：兩個入口讀同一份週報說明。實線是這次讀到的本人操作。",
)}
{gears([
    (True, "時間到就動", "每天早上週報草稿。案例 5。"),
    (False, "外面一推就動", "這段沒看到。"),
    (False, "進出關卡", "這段沒看到。"),
    (False, "推上去就上線", "這段沒看到。"),
    (False, "倒下拉起來", "這段沒看到。"),
])}
<p class="note">沒看到只代表這 14 天沒動到。覆蓋度不是分數。一顆排程齒輪加上一份 skill，已經能支持第 4 級。</p>
<h3>四項系統檢查</h3>
{checks([
    (False, "還沒測", "只看文件做得完嗎"),
    (False, "還沒測", "資料不齊會停嗎"),
    (False, "量還少 · 不擋級", "沒人盯著還在跑"),
    (False, "檔頭還沒寫", "出事找得到人"),
])}
<div class="scroll">
<table>
<thead><tr><th>檢查什麼</th><th>狀態</th><th>根據什麼，或還缺什麼</th></tr></thead>
<tbody>
  <tr><td>1. 只看文件，陌生人做得完嗎</td><td><span class="tag na">還沒測</span></td>
      <td>需要一個沒有舊記憶的環境，這次沒跑</td></tr>
  <tr><td>2. 資料不齊或算錯時會停嗎</td><td><span class="tag na">還沒測</span></td>
      <td>還沒做隔離測試</td></tr>
  <tr><td>3. 沒人盯著還能持續跑嗎</td><td><span class="tag warn">有排程、量還少</span></td>
      <td>8 則都在他還會看的時段，不能算系統營運</td></tr>
  <tr><td>4. 出事找得到人嗎</td><td><span class="tag na">檔頭還沒寫</span></td>
      <td>這就是本週要補的那一件</td></tr>
</tbody>
</table>
</div>
<p class="note">四項沒過不自動降回第 3 級。第 5 級要等例外迴路真的在用，不是把格子填滿。</p>

<h2 id="s5">五、值得留下的做法</h2>
<div class="scroll">
<table>
<thead><tr><th>做法</th><th>現在怎麼用</th><th>以後可以怎麼用</th><th>下一步</th></tr></thead>
<tbody>
  <tr>
    <td>走通之後寫成 SKILL，下一則只補差異（案例 1）</td>
    <td>已經在用</td><td>FAQ 模板也改走這條，不要手貼</td><td>維持週報；FAQ 下次再搬</td>
  </tr>
  <tr>
    <td>排程打開前先用舊稿跑一遍（案例 2）</td>
    <td>已經在用</td><td>任何會自己跑的東西都先走這關</td><td>維持</td>
  </tr>
  <tr>
    <td>兩個入口讀同一份說明，不各抄一份（案例 3）</td>
    <td>已經在用</td><td>新入口只接同一份檔</td><td>維持。不必為了報告再接一家</td>
  </tr>
</tbody>
</table>
</div>

<h2 id="s6">六、給本人與主管的結論</h2>
<ol>
  <li><strong>現在的位置：</strong>有效做法已經留下，也開始有一點自己跑。這一級過了。還不是系統級營運。</li>
  <li><strong>下週只做一件事：</strong>週報 skill 檔頭補維護人、版本、怎樣算能貼、出錯寫給誰。</li>
  <li><strong>請留下的習慣：</strong>啟用前用舊稿測一遍。這比多接一個入口更接近下一級。</li>
</ol>
"""


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "lv1.html").write_text(page(
        "lv1.html",
        "AI 幾級了示範｜LV1 換句話重問",
        "虛構示範。只用網頁版聊天、覺得不對就再問一次時，AI 幾級了的報告會長這樣。",
        BODY_LV1,
    ), encoding="utf-8")
    (DOCS / "lv3.html").write_text(page(
        "lv3.html",
        "AI 幾級了示範｜LV3 精準下指令",
        "虛構示範。交代清楚、會指出錯、會驗證、還沒留下模板時，AI 幾級了的報告會長這樣。",
        BODY_LV3,
    ), encoding="utf-8")
    (DOCS / "lv4.html").write_text(page(
        "lv4.html",
        "AI 幾級了示範｜LV4 模組化使用",
        "虛構示範。做法寫成 skill、有一點排程、系統還沒自己營運時，AI 幾級了的報告會長這樣。",
        BODY_LV4,
    ), encoding="utf-8")
    print("wrote", DOCS / "lv1.html")
    print("wrote", DOCS / "lv3.html")
    print("wrote", DOCS / "lv4.html")


if __name__ == "__main__":
    main()
