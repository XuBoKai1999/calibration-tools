# 校正文件管理工具實作步驟

`arch.md` 定義穩定架構、責任、storage model 與 data flow；本文件只定義施工順序與完成條件。

## 實作規則

> 如無必要勿增實體。

- 只實作 `CURRENT` step；功能首次出現時才建立 module。
- 依賴固定為 `GUI → feature logic → storage/config`。
- 不預建 Manager、Controller、Repository、Factory、DTO 或 system class hierarchy。
- 每一步完成後執行 tests、啟動 GUI、驗證完成條件並同步文件。

## Step 0 — Existing hardening

**Status: DONE**

已完成：薄 `main.py`、責任分離、runtime data 移出 Git、Case 非破壞式更新、schema-version 與未知頂層欄位保護、OCR confidence、staging cleanup、system config 最低語意驗證、GUI scale／geometry 記憶及相關測試。

Repository privacy、移除既有敏感檔與 rewrite Git history 是外部維護工作，不屬於 application development step；執行前需另行確認與備份。

## Step 1 — Case lifecycle and Case Workspace

**Status: CURRENT**

```text
New Case
→ 選擇 E05 / E07 / E27
→ manual 或 OCR
→ review
→ 明確儲存
→ 立即出現在正確 History
→ 開啟 Case Workspace
```

Workspace 提供「基本資料、歷史資料、本次量測、不確定度、產生報告、刪除案件」。基本資料沿用現有表單，其他區可先作 placeholder；header 顯示 Case ID、system、DUT 與 status。

Case 實體改按 system 分組為 `<data_root>/cases/<system>/<case_id>/`，不預建空子目錄。刪除必須確認、只刪選定 Case、刷新 History 並回到有效畫面。此步不做 uncertainty 或 report generation。

**Complete when:** manual/OCR 兩條路徑都先選 system；儲存後可從正確 system History 重新開啟 workspace；safe deletion 通過測試。

實作與自動測試已完成；待使用者依實際桌面流程驗收後，才將本 Step 標為 DONE 並推進 Step 2。

## Step 2 — Historical/reference import and Case snapshot

**Status: NEXT**

支援來源：previous managed Case，以及 imported legacy reference。使用者選定後：

```text
copy previous raw/report
→ current Case/reference/
```

保存最小 `meta.json` provenance。Case 沒有 reference 仍可工作，也可在建立後再選。此步不清理／解讀 raw data，不編輯 DOCX，且永不修改 reference snapshot。

**Complete when:** 兩種來源都能產生獨立 snapshot；原始來源移動或改變後，Case-local reference 仍可用。

## Step 3 — Define canonical raw-data format

**Status: LATER**

必須使用真實 E27 歷史 raw data，先辨認 reusable structure 與 previous measurement values，再定義如何產生不含舊觀測值的本次 template。之後才更新 `measurement_schema.json` 與 canonical `measurement/raw.csv`；不得預造最終 CSV schema。

**Complete when:** 格式由實際 E27 資料驗證，歷史測值不會進入本次 measurement。

## Step 4 — Measurement Workspace

**Status: LATER**

實作左側唯讀 previous/reference、右側可編輯 current measurement、結果區 current processed result。歷史 raw data 與 report 必須容易外部開啟；本次資料只存入 Case。

**Complete when:** reference 保持唯讀，本次輸入可保存並重開。

## Step 5 — Calculation and uncertainty

**Status: LATER**

優先完成 E27 的第一條 direct-measurement end-to-end flow：

```text
measurement/raw.csv
→ processing
→ result
→ uncertainty
→ expanded uncertainty
```

只實作真實資料需要的 mathematical primitives。`calculation.json` 只供參數與 declarative configuration，不執行任意 expression。

**Complete when:** E27 可由 Case-local data 重算結果與 expanded uncertainty，且 calculation code 不依賴 GUI。

## Step 6 — Report generation

**Status: LATER**

```text
reference report
→ copy
→ current report
→ 修改 current copy
```

永不修改 reference report。current report 使用 Case、current measurement result 與 uncertainty；沒有 previous report 時允許推薦或另選同 system template。不要求內嵌 Word editor。

**Complete when:** 可產生獨立 current report，reference hash/content 保持不變。

## Step 7 — E05 / E07 / E27 specific refinement

**Status: LATER**

通用流程完成後，才依實際程序加入 system-specific calculation。沒有真實需求就不建立特殊 abstraction。

## Step 8 — Historical automation / convenience

**Status: LATER**

視實際工作證明有用時再加入 previous-Case matching、raw normalization、template selection 與 comparison convenience。自動推薦只能 advisory，不能阻擋新 DUT 或取代人工選擇。

## Step 9 — LIMS integration

**Status: LATER**

LIMS integration 保持在 core measurement 與 uncertainty logic 之外，不得成為 Case workflow 的前置條件。
