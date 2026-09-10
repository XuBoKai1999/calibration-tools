# 校正文件管理工具架構

## 1. 穩定產品流程

```text
New Case
→ 選擇校正系統
→ 輸入基本資料
→ 建立 Case
→ 取得可用的前次／參考資料
→ 本次量測
→ 計算與不確定度
→ 產生報告
→ 保存完整 Case
```

目前支援 E05、E07、E27；現階段一律視為直接量測系統。差異先由 capability、pricing、measurement schema、calculation configuration 與 output quantities 表達。只有未來確有不同演算法時，才考慮 system-specific code；不預建 E05/E07/E27 class hierarchy。

## 2. 核心原則與依賴

> 如無必要勿增實體。

Case folder 中的資料是 source of truth。SQLite 若出現，只作可重建索引。功能尚未出現時不建立空 module，也不引入 Manager、Controller、Repository、Factory、DTO、ORM、workflow engine 或 event bus。

```text
GUI
 ↓
Cases / Intake / Measurement / History / Reports
 ↓
Storage / System Config
```

storage、OCR、measurement、uncertainty、report 不得 import GUI。`main.py` 只負責建立 application、少量 application-level dependency、主視窗及 event loop。

## 3. 建案與 Case Workspace

### 3.1 New Case

```text
Home
↓
New Case
↓
選擇 E05 / E07 / E27
↓
選擇 manual entry 或 OCR reservation form
↓
檢查／修改基本資料
↓
明確儲存並建立 Case
↓
立即出現在所選系統的 History
↓
開啟 Case Workspace
```

OCR 只是填入 Case 基本資料的方法之一，不定義 Case lifecycle，也不應暗中決定 system。system 從建案開始就是 Case identity 的一部分。OCR staging 未經人工確認不得成為正式 Case 資料；低信心欄位留白。

### 3.2 Case Workspace

開啟 Case 後進入可工作的 workspace，而非只顯示基本資料的 dead end：

```text
基本資料 | 歷史資料 | 本次量測 | 不確定度 | 產生報告 | 刪除案件
```

畫面至少清楚顯示 Case ID、system、DUT／item name，以及適用時的 status。既有基本資料表單成為「基本資料」區；尚未實作的區域可暫作 placeholder。

刪除案件是危險操作：必須確認、只刪選定 Case、刷新 History，並回到有效畫面。不為此建立 CaseManager。

## 4. 程式責任

| 責任 | 位置 | 規則 |
| --- | --- | --- |
| bootstrap | `main.py` | 不含業務、I/O 或頁面實作 |
| GUI | `gui/` | 顯示、輸入、navigation、window-level orchestration |
| Case | `cases/model.py` | Case 資料模型 |
| Case storage | `cases/storage.py` | folder、JSON、Case-local file copy |
| Case operations | `cases/service.py` | 建立、儲存及 Case-level operations |
| OCR | `intake/ocr.py` | image → structured OCR result |
| reservation intake | `intake/reservation.py` | normalize、欄位 mapping、staging |
| system config | `systems/loader.py` | 集中讀寫與驗證設定 |
| future features | `measurement/`、`uncertainty/`、`history/`、`reports/`、`legacy/` | 功能首次出現時才建立 |

GUI 編輯既有 Case 時只更新自己負責的欄位，不得 reconstruct 後消滅未顯示資料。Case loader 必須拒絕不支援的 schema version 與未知頂層欄位，不能 silent data loss。

## 5. Runtime storage

Runtime data 位於作業系統 application data 目錄，不放進 Git repository。目標結構依 system 分組：

```text
<data_root>/
├── inbox/
├── cases/
│   ├── E05/<case_id>/
│   ├── E07/<case_id>/
│   └── E27/<case_id>/
├── references/
│   ├── E05/
│   ├── E07/
│   └── E27/
└── index/                 # 真正建立索引時才出現
```

- `cases/`：本 application 正式管理的校正案件。
- `references/`：application 出現以前的歷史材料，或另行維護的歷史來源／archive。
- historical reference 不會自動變成 Case，也不為了套入 Case model 而製造假 Case。

成熟 Case 的概念結構：

```text
cases/<system>/<case_id>/
├── case.json
├── reservation/
├── reference/
│   ├── meta.json
│   ├── raw.<format>
│   └── report.docx
├── measurement/
│   ├── raw.csv
│   └── result.json
└── report/
    └── <current-report>.docx
```

不預建空目錄；只在實際需要時建立。測試使用 temporary directory 與虛構資料，真實預約單及案件資料不得作 fixture。

## 6. Historical/reference material

來源可為前一個 managed Case，或 `references/<system>/` 中的 legacy item。使用者選定後，raw data 與 report 必須複製到當前 Case，不能只記外部路徑：

```text
historical source
      ↓ copy
current Case/reference/
```

Case-local `reference/` 是該案件實際採用的 immutable snapshot；global `references/` 是 archive/source。不得原地修改 `reference/` 內檔案。沒有歷史材料時 Case 仍須可用，且建立後也能稍後選擇 reference。

`reference/meta.json` 只保存必要 provenance，例如：

```json
{
  "source_type": "case or legacy_reference",
  "source_id": "...",
  "previous_report_number": "...",
  "raw_file": "...",
  "report_file": "..."
}
```

不為這份 metadata 建立 ReferenceManager。

選擇訊號可包括 previous report number、相同 DUT／serial number、manual selection 與同 system 近期項目。建議順序是「相同 DUT／明確報告 → 使用者選擇 → 近期同系統」，但自動推薦只能 advisory；使用者能接受、另選或完全不使用 reference，新 DUT 不得被阻擋。

## 7. Measurement workspace 與 raw data reuse

```text
┌────────────────────────┬────────────────────────┐
│ Previous / Reference   │ Current Measurement    │
│ read-only              │ editable               │
│ old raw data / report  │ current raw data       │
└────────────────────────┴────────────────────────┘
                ↓
       processed result
                ↓
           uncertainty
```

Qt widget 與精確 layout 不屬於架構規格；必要行為是左側可查看／開啟唯讀歷史 raw data 與 report，右側輸入本次量測，結果區顯示本次 processed values 與 uncertainty。

`reference/raw.*` 與 `measurement/raw.csv` 永遠是不同檔案。若沿用前次結構，只保留 calibration points、measurement configuration 與 field structure，必須移除前次 observations、measured values 與 calculated results；歷史數值不得靜默變成本次數值。

最終 canonical CSV 尚未定義，必須由真實 E27 歷史 raw data 決定，本文件不預造 schema。

## 8. System configuration

```text
config/systems/<system>/
├── system.json
├── capability.json
├── pricing.json
├── measurement_schema.json
└── calculation.json
```

| 檔案 | 責任 |
| --- | --- |
| `capability.json` | range、quantities、restrictions、valid coverage |
| `pricing.json` | pricing／service rules |
| `measurement_schema.json` | 量測資料結構；不是歷史或本次量測值 |
| `calculation.json` | output/measurand、所需參數、uncertainty components、現有 B 類標準不確定度 |

設定只提供 declarative parameters 與 calculation primitives；計算仍由程式碼實作。禁止以 JSON 儲存任意 Python expression 或使用 `eval()`。

## 9. Measurement、uncertainty 與 report

```text
raw observations
→ measurement processing
→ measurement result
→ uncertainty calculation
→ combined standard uncertainty
→ expanded uncertainty
```

第一版只實作真實程序需要的 primitive，例如 mean、standard deviation、Type A、DUT resolution、rectangular distribution、system B-type standard uncertainty、expanded-to-standard conversion、RSS 與 expanded uncertainty。regression、divider equation、ratio/phase error、correlation 與特殊 correction model 等，等實際 system requirement 出現才加入。

前次 report 永不直接修改：

```text
case/reference/report.docx
→ copy
case/report/<current-report>.docx
→ 修改 current copy
```

current report 未來可填 current customer、DUT、report number、calibration date、measurement results、expanded uncertainty 與 notes。新 DUT 沒有前次 report 時，可推薦同 system 的近期 template，但使用者可另選。現階段允許用外部程式開啟 DOCX，不要求內嵌 Word viewer/editor。

## 10. 實作狀態

### 已實作

- 薄 `main.py`、主要 GUI pages、navigation、GUI scale 與 QSettings。
- Case model/storage/service、人工與 OCR 基本資料建案。
- OCR confidence filtering 與 staging cleanup。
- Case non-destructive GUI update、schema-version 與未知頂層欄位保護。
- E05/E07/E27 基本 config 載入、編輯與最低語意驗證。
- runtime data 移出 repository。

### 穩定目標但尚未完成

- 先選 system 的完整 New Case flow 與 Case Workspace。
- Case 實體路徑由目前的年度層改為 `cases/<system>/<case_id>/`。
- safe deletion、references archive、Case-local reference snapshot。
- canonical measurement format、measurement workspace、calculation、uncertainty 與 report generation。
- `calculation.json`。
