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

已完成：薄 `main.py`、責任分離、repository-local `data/` 完整 Git ignore、Case 非破壞式更新、schema-version 與未知頂層欄位保護、OCR confidence、staging cleanup、system config 最低語意驗證、GUI scale／geometry 記憶及相關測試。

Repository privacy、移除既有敏感檔與 rewrite Git history 是外部維護工作，不屬於 application development step；執行前需另行確認與備份。

## Step 1 — Case lifecycle and Case Workspace

**Status: AWAITING INDEPENDENT DESKTOP ACCEPTANCE**

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

實作與自動測試已完成；待使用者依實際桌面流程驗收後，才將本 Step 標為 DONE。

## Data preparation — Historical schema audit

**Status: DONE**

在實作 reference import 或 canonical format 前，先唯讀審查 E05／E07／E27 的代表性 `past/<system>/source/` 真實檔案，辨識結構世代、RAW、Case／環境／setup、system／calculation config、derived 及 unresolved 欄位。特別查明 E05 客戶儀器資訊來源與 E07 burden／frequency／range 的層級。

本任務只產生審查結果；審核前不 batch-clean，不實作 measurement、uncertainty 或 report generation。

三系統與跨系統結果已記錄於 `past/E05/schema-audit.md`、`past/E07/schema-audit.md`、`past/E27/schema-audit.md`、`past/schema-comparison.md`，並已完成人工 review。

**Complete when:** 三系統的代表性結構、欄位分類、report-only 資訊、未解問題，以及三檔命名提案是否足夠均有可人工審閱的記錄。（已完成）

## Data preparation — Canonical historical format

**Status: DONE**

已核定一筆一目錄的 package：`manifest.json` 必有，`raw.csv`、`context.csv`、`report.docx` 依來源存在。RAW 一個 observation 一列；CONTEXT 使用 scoped long form；system/procedure CONFIG 與可重算 DERIVED 不重複進 Case。規格見 `past/canonical-format.md` 與三系統 `clean-schema.md`。

## Data preparation — Representative cleaner validation

**Status: PAUSED — REVISED PROTOTYPE OUTPUT AWAITING FINAL HUMAN REVIEW**

依每個 audited generation 選最多 2～3 件代表樣本，實作 cleaner dry-run；逐件人工比對 source 與 clean，加入 invariant／round-trip tests。遇到未知 sheet、side table、欄位、單位或 mapping 必須 fail／unresolved，不得靜默略過。代表樣本核准前不得批次轉換 2,918 份 workbook。

針對人工驗收發現的 context/provenance 問題已修正於 `tools/historical_cleaner.py`。同一組 14 件只重新產生於 ignored `past/_dryrun/`：10 件 `PASS_WITH_UNRESOLVED`、4 件 `FAIL_AMBIGUOUS`，沒有 unconditional PASS。完整 repository tests 38/38 通過。下一步依 `past/_dryrun/manual-review.md` 重驗八件；production batch 仍禁止。

**Complete when:** 每個支援 generation 的代表 package 通過人工比對及自動 invariant tests，且所有不支援結構明確失敗或列為 unresolved。

## Data preparation — Report fields and system revisions

**Status: DONE**

已完成 recent report audit：E05 24 件、E07 24 件、E27 19 件可用 DOCX。結果支持 RAW / CASE / SYSTEM_REVISION / DERIVED / STATIC_TEMPLATE 分層；E05 證實 2025 年 9 月中有非年度 revision 邊界，selected standard 應為 Case reference，標準器與證書本體屬 revision。2024 legacy `.doc` 尚無可用語意讀取途徑。下一步先 review audit，再定 minimum CASE contract 與 revision-selection semantics；尚不建立 revision JSON。

## Data preparation — Architecture realignment

**Status: DONE**

已將 report-driven 結論寫回 `arch.md` 與 historical canonical/clean-schema 說明：raw workbook 不重建完整 Case；Reservation/Case、Measurement、System Revision、Derived、Report 各自負責不同資料；報告只要求實際 section/template 所需欄位，缺值才提示使用者。

## Data preparation — Minimum report-variable contracts

**Status: CURRENT — SPECIFICATION ONLY**

下一步按 E05/E07/E27 的實際 measurement section 定義最小 report variables，逐欄標明來自 Case JSON、Measurement、System Revision、Derived 或互動補值，並同時定義 revision identity/effective-date selection semantics。不要建立 Settings/revision JSON，也不要實作 parser/UI。

**Complete when:** 每個 observed report section 的條件必填欄位與來源責任明確，且 combined E05/E07 report 能分別綁定其適用 revision。

## Data preparation — Simplify historical cleaner target

**Status: NEXT**

依 report-variable contract 縮減 cleaner：raw workbook 只保留 irreducible observations 與必要 setup semantics；Case/report metadata 只在確有最低報告需求且其他來源缺少時另由小型 report parser 回收。先重做代表樣本驗收，再考慮 batch/quarantine。

## Data preparation — Case/report field resolution

**Status: THEN**

規格化 report generation 如何依序從 Case JSON、Measurement、bound System Revision、Derived 取得 required variables，並只提示仍缺少的欄位；確認值適合時寫回 Case JSON。不另建 report metadata database。

## Data preparation — Versioned System Settings

**Status: THEN**

在 field ownership 與 revision binding 核准後，才設計可年中生效且不回溯改寫舊 Case 的 System Revision／Settings。此階段才決定實體格式，不預設 `2024.json`／`2025.json`／`2026.json`。

## Step 2 — Historical/reference import and Case snapshot

**Status: AFTER REPRESENTATIVE CLEANER VALIDATION**

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

依 applicable template/measurement sections 取得 required variables，依序由 Case JSON、Measurement、bound System Revision 與 Derived 解決，只要求使用者補齊仍缺少的條件欄位，再產生獨立 current report。reference report 永不修改，且不是 current report 的資料來源；沒有 previous report 也能工作。不要求內嵌 Word editor。

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
