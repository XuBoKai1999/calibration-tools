# 校正文件管理工具架構

## 1. 目標與生命週期

建立以 PySide6 GUI 操作的校正案件管理工具，先支援 E05（直流高壓）、E07（交流高壓）與 E27（片電阻）。

```text
預約 → 建案 → 收件 → 量測 → 計算 → 報告 → 結案
```

| 階段 | 主要功能 |
| --- | --- |
| 預約 | 月曆、查看空檔、案件排程 |
| 建案 | 預約單圖片、OCR、人工確認、歷史搜尋、能力驗證、報價 |
| 收件 | 報告編號、確認 DUT、校正點與解析度 |
| 量測 | 多日資料、環境條件、raw data、歷史 raw data 對照 |
| 計算 | 數據整理、A 類、B 類、DUT resolution、擴充不確定度 |
| 報告 | report notes、template、欄位填入、DOCX/PDF |
| 結案 | 狀態更新、保存、歷史索引 |

橫跨生命週期的功能包括 Case storage、system configuration、history/index、settings、legacy import、file preview/open 與 GUI navigation。

## 2. 核心原則

### 2.1 Case 是正式資料核心

一個校正案件是一個 `Case`，並對應一個獨立資料夾。Case 資料夾中的 JSON、CSV 與文件是 source of truth；SQLite 未來只作可重建的搜尋索引。

### 2.2 Template、歷史資料與 OCR 都只是來源

```text
System Template ─┐
History ─────────┼→ 人工確認 → Case
OCR staging ─────┘
```

所有帶入值皆可人工修改。建立 Case 後，實際工作只使用 Case 內版本；外部 template 或歷史檔案的變動不得污染既有案件。

### 2.3 如無必要勿增實體

先定義完整責任邊界，但只有功能實際出現時才建立 module 或 class。簡單函式、dataclass、JSON、CSV 足以完成時，不引入 ORM、workflow engine、event bus、DI、web API、plugin system 或 background service。

不要因為名稱整齊就預建 `Manager`、`Controller`、`Repository`、`Factory` 或空目錄；也不能以精簡為由把不同責任塞回 `main.py`。

## 3. Dependency direction

```text
GUI
 ↓
Case / Intake / Measurement / History / Reports
 ↓
Storage / System Config
```

禁止反向依賴：OCR、storage、uncertainty、report 不得 import GUI。業務邏輯與檔案處理必須能在沒有 GUI 的環境下測試。

## 4. 程式責任

完整責任地圖如下；這是 architecture definition，不代表所有 module 現在都必須存在。

```text
src/calibration_manager/
├── gui/
│   ├── main_window.py
│   ├── pages/
│   │   ├── home_page.py
│   │   ├── calendar_page.py
│   │   ├── history_page.py
│   │   └── case_page.py
│   └── dialogs/                  # 有實際 dialog 時才建立
├── cases/
│   ├── model.py
│   ├── storage.py
│   └── service.py
├── intake/
│   ├── ocr.py
│   └── reservation.py
├── measurement/                 # 實作量測時建立
│   ├── storage.py
│   └── processing.py
├── uncertainty/                 # 實作不確定度時建立
│   └── engine.py
├── systems/                     # 實作系統設定時建立
│   ├── loader.py
│   ├── capability.py
│   └── pricing.py
├── history/                     # 實作索引時建立
│   └── index.py
├── reports/                     # 實作報告時建立
│   └── generator.py
├── legacy/                      # 實作舊檔匯入時建立
│   ├── excel.py
│   └── word.py
└── settings.py
```

### 4.1 `main.py`

`main.py` 只作 application bootstrap：建立 `QApplication`、設定 application identity 與 data path、建立 `MainWindow`、啟動 event loop。它不知道 OCR、Case JSON、E05 規則、不確定度或報告如何運作。

### 4.2 `gui/`

只負責顯示資料、接收輸入、切頁並呼叫其他模組。`MainWindow` 管主框架、navigation、window geometry 與 GUI scale；各 Page 管自己的 layout、widgets 與頁面內互動。GUI 不自行序列化 JSON 或計算 uncertainty。

### 4.3 `cases/`

- `model.py`：定義 `Case` 及其 customer、instrument、status、schedule、calibration request 等資料。
- `storage.py`：Case folder、`case.json` load/save、複製檔案進 Case。
- `service.py`：建立 Case、產生 Case ID、確認並儲存 Case、Case 級操作。

若其中一個檔案日後再混合兩個明顯責任才繼續拆；不增加 CaseManager、CaseRepository 等同義包裝。

### 4.4 `intake/`

- `ocr.py`：只做 `image → structured OCR result`。
- `reservation.py`：預約單欄位 mapping、normalize、缺欄位處理與 staging。

OCR 不建立 Case、不寫 `case.json`、不決定 Case folder，也不更新 GUI。

### 4.5 後續責任

- `measurement/`：量測日、`environment.json`、`raw.csv` 與 raw data processing；不計算 uncertainty。
- `uncertainty/`：A 類、B 類、DUT resolution、combined 與 expanded uncertainty。
- `systems/`：載入 system config、能力與報價；不建立 E05/E07/E27 class，除非未來確有不同演算法。
- `history/`：建立、重建及查詢 SQLite index；只回答找到哪些 Case，不負責匯入。
- `reports/`：由 Case、processed data、uncertainty 與 template 產生 DOCX/PDF；report notes 仍屬 Case data。
- `legacy/`：解析舊 Excel/Word；只回傳解析資料，由 Case service 決定匯入與保存。
- `settings.py`：少量 QSettings key、GUI scale、window geometry 與 data path policy；不建立 settings manager。

## 5. 資料架構

```text
data/
├── inbox/
├── cases/
└── index/                       # 建立歷史索引時才出現

config/
└── systems/
    ├── E05/
    ├── E07/
    └── E27/

templates/                       # 建立正式報告模板時才出現
```

上述目錄都只在真正寫入資料時建立，不預建大量空目錄。

### 5.1 OCR staging 與建案

```text
照片
 ↓
data/inbox/<temporary-id>/
├── original.<ext>
└── parsed.json
 ↓
人工確認與修改
 ↓
Case service
 ├── storage 寫入 case.json
 └── storage 複製 reservation files
```

`parsed.json` 是暫存辨識結果，不是正式 Case 資料。人工確認後的表單值才寫入 `case.json`。

### 5.2 Case folder

```text
data/cases/<year>/<system>/<case_id>/
├── case.json
├── reservation/
│   ├── original.<ext>
│   └── parsed.json
├── reference/
├── measurement/
│   └── day_01/
│       ├── environment.json
│       └── raw.csv
├── uncertainty/
│   └── uncertainty.json
├── processed/
└── report/
    ├── report.docx
    └── report.pdf
```

只在使用時建立子目錄。大型 raw data 不放進 `case.json`；環境 metadata 不塞進 CSV 前幾列。

### 5.3 功能與資料對應

| 功能 | 程式 | 資料 |
| --- | --- | --- |
| OCR | `intake/ocr.py` | `data/inbox/` |
| 預約解析 | `intake/reservation.py` | staging `parsed.json`、Case `reservation/` |
| Case | `cases/` | `case.json` |
| 多日量測 | `measurement/` | `measurement/` |
| uncertainty | `uncertainty/` | `uncertainty/` |
| 歷史搜尋 | `history/` | `data/index/` |
| 系統能力與報價 | `systems/` | `config/systems/` |
| report | `reports/` | `report/`、`templates/` |
| legacy | `legacy/` | Case `reference/` |

## 6. GUI 規則

- 使用 PySide6 layout manager，避免大量 absolute positioning。
- 支援 Windows DPI scaling、GUI scale、快捷鍵與 Ctrl+滑鼠滾輪。
- 使用 `QSettings` 記住倍率、主視窗大小與位置。
- 高倍率或小視窗使用 scroll area，不能出現明顯 overlap 或文字裁切。
- OCR、自動帶入與歷史匯入的資料都必須可人工覆寫。

## 7. 完成條件

- 沒有歷史案件時仍可完整工作。
- 每個 Case 都能獨立保存、載入與重現。
- template 更新不影響既有 Case。
- OCR 未經人工確認不成為正式資料。
- Case storage、uncertainty、pricing 與 report generation 可脫離 GUI 測試。
- SQLite 刪除後可由 Case folders 重建。
- E05、E07、E27 共用主架構，但保留各自設定與計算差異。
