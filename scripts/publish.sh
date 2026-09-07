#!/usr/bin/env bash
# ai-level-check / publish.sh
#
# 把一期的報告推進團隊的 private repo。推上去之後 git 歷史刪不掉，
# 這正是這套機制有公信力的原因，也正是它需要小心的原因。
#
#   ./scripts/publish.sh --period 2026-W36 --repo git@github.com:your-org/ai-level-log.git
#   ./scripts/publish.sh --period 2026-W36 --repo <url> --report reports/2026-W36.html --yes
#
# 這支腳本刻意做不到的事：
#   - 不 force push、不改寫歷史、不刪既有檔案
#   - 不會把 evidence/ 原始紀錄推上去（只推報告）
#   - 沒有 --yes 就一定會停下來讓你確認

set -euo pipefail

PERIOD=""
REPO=""
REPORT=""
NAME="${AI_LEVEL_NAME:-$(whoami)}"
ASSUME_YES=0

die() { printf '\033[31m錯誤：\033[0m%s\n' "$1" >&2; exit 1; }
info() { printf '  %s\n' "$1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --period) PERIOD="${2:-}"; shift 2 ;;
    --repo)   REPO="${2:-}"; shift 2 ;;
    --report) REPORT="${2:-}"; shift 2 ;;
    --name)   NAME="${2:-}"; shift 2 ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) die "不認得的參數：$1" ;;
  esac
done

[[ -n "$PERIOD" ]] || die "缺 --period，例如 --period 2026-W36"
[[ -n "$REPO" ]]   || die "缺 --repo，例如 --repo git@github.com:your-org/ai-level-log.git"

# 找報告檔
if [[ -z "$REPORT" ]]; then
  for cand in "reports/${PERIOD}.html" "reports/${PERIOD}.md" "reports/${NAME}-${PERIOD}.html"; do
    [[ -f "$cand" ]] && REPORT="$cand" && break
  done
fi
[[ -n "$REPORT" && -f "$REPORT" ]] || die "找不到報告檔。用 --report 指定路徑，或先產出 reports/${PERIOD}.html"

# 安全檢查：報告裡不該混進金鑰
if grep -qE '(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})' "$REPORT"; then
  die "報告裡疑似含有 API 金鑰，已中止。先處理掉再推。"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo
echo "準備推送："
info "期間　　：$PERIOD"
info "報告　　：$REPORT ($(wc -c < "$REPORT" | tr -d ' ') bytes)"
info "推到　　：$REPO"
info "路徑　　：reports/${NAME}/${PERIOD}$(basename "$REPORT" | sed 's/.*\././')"
echo
echo "推上去之後，這份報告會永久留在 git 歷史裡，改不掉也刪不乾淨。"
echo "確認你看過這一版的內容，而且該遮的都遮了。"
echo

if [[ "$ASSUME_YES" -ne 1 ]]; then
  read -r -p "確定要推嗎？輸入 yes 繼續：" ans
  [[ "$ans" == "yes" ]] || die "已取消，沒有推送。"
fi

git clone --depth 1 "$REPO" "$WORK/repo" 2>/dev/null \
  || die "clone 失敗。確認 repo 存在、而且你有寫入權限。"

EXT="${REPORT##*.}"
DEST_DIR="$WORK/repo/reports/${NAME}"
DEST="${DEST_DIR}/${PERIOD}.${EXT}"
mkdir -p "$DEST_DIR"

if [[ -f "$DEST" ]]; then
  echo
  echo "這一期已經推過了：reports/${NAME}/${PERIOD}.${EXT}"
  echo "覆蓋等於改寫既有紀錄。要補一版就換一個期間代號，例如 ${PERIOD}-r2。"
  die "已中止，沒有覆蓋。"
fi

cp "$REPORT" "$DEST"

cd "$WORK/repo"
git add "reports/${NAME}/${PERIOD}.${EXT}"

# 只允許加報告；任何其他異動都表示有東西不該進來
STAGED="$(git diff --cached --name-only)"
if [[ "$(echo "$STAGED" | wc -l | tr -d ' ')" -ne 1 ]]; then
  die "暫存區不只一個檔案，已中止：$STAGED"
fi

SHA="$(shasum -a 256 "$DEST" | cut -d' ' -f1 | cut -c1-16)"
git commit -q -m "report(${NAME}): ${PERIOD}

報告來源：ai-level-check
內容雜湊：sha256:${SHA}
產出時間：$(date '+%Y-%m-%d %H:%M %Z')"

git push -q origin HEAD || die "push 失敗。可能是沒有權限，或遠端有保護規則。"

echo
echo "已推送：reports/${NAME}/${PERIOD}.${EXT}"
info "commit：$(git rev-parse --short HEAD)"
info "雜湊　：sha256:${SHA}"
echo
