---
name: 新增紀錄來源
about: 想支援 Cursor、Gemini、Antigravity 或公司內部的 AI 工具
title: "[collector] 支援 <工具名稱>"
labels: collector
---

## 工具

- 名稱與版本：
- 平台：<!-- macOS / Windows / Linux -->

## 紀錄位置

<!-- 絕對路徑，用 ~ 代替家目錄。例如 ~/.foo/sessions/*.jsonl -->

## 格式

<!-- JSONL / SQLite / JSON / 其他。貼一筆去識別化的範例。 -->

## 欄位分布（實測，必填）

<!-- 掃過幾個檔案？關鍵欄位各有哪些值、各幾筆？

例如：
| originator | 數量 |
| codex_exec | 2797 |
| Codex Desktop | 223 |

沒有實測數字的 collector 不會合併——猜出來的欄位會讓所有下游判斷一起錯。 -->

## human / automation / subagent 怎麼分

<!-- 哪個欄位可以分辨「人在鍵盤前打的字」與「程式驅動的對話」？
如果這個工具沒有這種欄位，說明你打算怎麼判斷，以及誤判的風險。 -->

## 工具呼叫與寫檔怎麼抓

<!-- 工具名在哪個欄位？寫檔的檔名怎麼取得？ -->

## 你會自己實作嗎

- [ ] 我會送 PR
- [ ] 我只回報格式，希望有人接手
