# 校正文件管理工具架構

## 1. 目標

建立一套以 **PySide6 GUI** 為主要操作介面的校正案件管理工具，先支援：

- E05：直流高壓
- E07：交流高壓
- E27：片電阻

主要流程：

```text
預約
→ 建立案件
→ 收件
→ 多日量測
→ 資料處理
→ 不確定度計算
→ 產生報告
→ 結案
```

未來可加入其他校正系統，但不要為尚未出現的需求預先建立抽象框架。

---

## 2. 核心原則

### 2.1 Case 是核心

一個校正案件就是一個 `Case`，並對應一個獨立資料夾。

Case 內應保存完成與重現該案件所需的重要資料，包括：

- 客戶與 DUT 資料
- 預約與報告編號
- 校正點
- 歷史參考資料
- 多日 raw data 與環境資料
- 本案 uncertainty
- DUT 解析度
- 報告附註
- 計算結果
- 最終報告

### 2.2 Template 與歷史資料都只作來源

```text
System Template → Copy → Case
History         → Optional Copy → Case
```

建立 Case 後，實際工作只使用 Case 內版本。

目的：

- template 更新不污染舊案件
- 舊案件搬移不破壞目前案件
- 每案可獨立修改與重現

歷史資料只能作為建議或參考，不得假設一定存在。

### 2.3 保留人工修改

任何可能因案件不同的資料都必須可手動輸入或覆寫，包括：

- 客戶與儀器資料
- 校正點
- DUT resolution
- uncertainty
- report notes
- 環境資料
- 本次與前次報告編號

自動帶入不得成為不可修改的值。

### 2.4 如無必要勿增實體

新增 class、module、service、database table 或其他抽象前，必須有明確且獨立的責任。

若簡單函式、dataclass、JSON、CSV 即可完成，就不要增加額外框架。

目前不要引入：

- ORM
- workflow engine
- event bus
- DI framework
- web API
- plugin system
- background service

---

## 3. 程式架構

程式依明確責任拆分，不以「少增實體」為理由把不同層級的工作集中在單一檔案，也不為尚未存在的功能預建企業式架構。

目前實際結構：

```text
main.py
src/calibration_manager/
├── settings.py
└── gui/
    ├── main_window.py
    └── pages/
        ├── home_page.py
        ├── calendar_page.py
        └── history_page.py
```

`cases.py`、`systems.py`、`case_page.py` 等檔案應在對應功能首次實作時才建立，不先建立空檔案。

### 3.1 `main.py`

`main.py` 保持為薄的 application bootstrap，只負責：

- 建立 `QApplication`。
- 初始化少量 application-level dependency。
- 載入必要設定。
- 建立主視窗。
- 啟動 event loop。

其內容應接近：

```python
def main():
    app = QApplication(...)
    settings = QSettings(...)
    window = MainWindow(settings)
    window.show()
    return app.exec()
```

`main.py` 不負責：

- Case JSON 或 CSV 讀寫。
- uncertainty 計算、pricing 或 report generation。
- calendar business logic。
- 大量 widget 定義或各頁面 UI implementation。

### 3.2 GUI

`MainWindow` 負責 application 主框架、頁面切換、window geometry、GUI scale 與 application-level UI state。不要把每個頁面的具體 widget 全部放進 `MainWindow`。

每個主要 Page 負責自己的 layout、widgets 與頁面內 UI interaction。Page 可發出操作意圖，但不直接實作大量檔案 I/O、資料序列化、uncertainty 或 pricing 計算。

現有頁面各自放在 `gui/pages/`。Case 頁面真正開始實作時才新增 `case_page.py`；目前不為其各 tab 預建空 class。

### 3.3 Model、storage 與 GUI

Case 功能出現時，最低責任分離為：

```text
model → 描述 Case 資料
storage → Case folder 與 JSON / CSV load、save
GUI → 輸入、操作與顯示
```

初期可將 Case model 與 storage 集中在 `src/calibration_manager/cases.py`。只有當它開始同時包含大量 model、storage 或 validation 邏輯時，再拆成 `cases/model.py`、`cases/storage.py`、`cases/validation.py`。

GUI 不自行實作 JSON serialization；storage 也不得 import GUI widget。不要預先建立 `CaseManager`、`CaseService`、`CaseRepository`、`CaseController` 或 `CaseFactory`。

### 3.4 Settings 與系統設定

少量 application-level 設定集中於 `settings.py`，GUI scale 與 window geometry 直接交由 `QSettings` 保存，不再包裝多層 settings subsystem。

E05、E07、E27 的技術資料仍放在 `config/systems/`。功能實際需要時，以單一 `systems.py` 作集中讀取入口；不要為各系統建立 Manager class。

### 3.5 依賴方向

```text
GUI
 ↓
application / domain logic
 ↓
file / config storage
```

storage 不得依賴 GUI。Case storage、uncertainty、pricing 與 report generation 應可在沒有 GUI 的環境下測試。

---

## 4. GUI

首頁只需要：

```text
首頁
├── 月曆
├── 歷史案件
└── 設定
```

### 月曆

用途：

- 依月份查看案件
- 顯示日期、系統、客戶、狀態
- 點選日期建立案件
- 點選案件進入 Case

### 歷史案件

先依：

```text
E05 / E07 / E27
```

分類，再支援搜尋：

- Case ID
- 報告編號
- 客戶
- 型號
- serial number
- 日期
- 狀態

### Case 頁面

建議分成：

```text
基本資料
歷史資料
量測
結果
不確定度
報告
```

量測支援多日：

```text
Day 1
Day 2
...
+ 新增量測日
```

### GUI 規則

- 使用 PySide6 layout manager。
- 不大量使用 `move()`、`resize()`、`setGeometry()`。
- 支援 Windows DPI scaling。
- 支援 GUI scale，並記住倍率。
- 記住主視窗大小與位置。
- 優先使用 `QSettings`。
- resize 或 scaling 後不得有明顯 overlap 或文字裁切。

---

## 5. Case 資料

建議目錄：

```text
cases/
└── 2026/
    └── E05/
        └── 2026-E05-00123/
            ├── case.json
            ├── reservation/
            ├── reference/
            ├── measurement/
            ├── uncertainty/
            ├── processed/
            └── report/
```

只在實際需要時建立子目錄，不建立大量空資料夾。

### `case.json`

只保存主要 metadata 與狀態，例如：

```json
{
  "schema_version": 1,
  "case_id": "2026-E05-00123",
  "system": "E05",
  "status": "reserved",

  "customer": {},
  "instrument": {},

  "schedule": {
    "reserved_date": "",
    "received_date": null,
    "completed_date": null
  },

  "report": {
    "previous_report_number": "",
    "current_report_number": "",
    "notes": []
  },

  "calibration_request": {
    "mode": "specified_points",
    "reference_report": null,
    "points": []
  }
}
```

不要把大型 raw data 塞進 `case.json`。

---

## 6. 量測、歷史資料與 Uncertainty

### 6.1 多日量測

每個量測日保存：

```text
measurement/day_01/
├── environment.json
└── raw.csv
```

`environment.json` 保存：

- 日期
- 操作者
- 溫度
- 濕度
- 起訖時間
- 備註

raw data 使用 CSV，欄位依校正系統決定。

不要把環境 metadata 塞進 CSV 前幾列。

### 6.2 歷史資料

找到前次案件後，可選擇匯入：

- 客戶與 DUT 資料
- 校正點
- DUT resolution
- report notes
- previous report
- previous raw data

若實際使用歷史文件作參考，複製到：

```text
reference/
```

不要只保存外部路徑。

舊 Word / Excel 不需要一次全部整理；需要時再嘗試轉換，且不得覆寫原始檔。

### 6.3 Uncertainty

每個系統可有：

```text
config/systems/E05/uncertainty_template.json
```

建立 Case 時複製成：

```text
Case/uncertainty/uncertainty.json
```

實際計算只使用 Case 內版本。

至少支援：

- A 類 uncertainty
- 系統共通 B 類
- DUT resolution
- 每案額外 B 類

DUT resolution 必須允許：

- 手動輸入
- 從歷史案件建議帶入
- 不同 range 使用不同 resolution

複雜計算邏輯寫在 Python，不把公式全部塞進 JSON。

---

## 7. 各校正系統設定

每個系統只保存真正共通的設定：

```text
config/systems/
├── E05/
│   ├── capability.json
│   ├── pricing.json
│   ├── measurement_schema.json
│   └── uncertainty_template.json
├── E07/
└── E27/
```

用途：

- `capability.json`：判斷指定校正點是否可執行
- `pricing.json`：報價
- `measurement_schema.json`：raw data 欄位
- `uncertainty_template.json`：通用 uncertainty

若客戶要求「同前次報告」，只把前次報告視為校正點來源，不建立另一套特殊流程。

---

## 8. 儲存與搜尋

案件資料夾中的 JSON / CSV / 文件是 source of truth。

可使用 SQLite 作搜尋索引，但只作：

```text
index / cache
```

例如索引：

- case_id
- system
- customer
- model
- serial number
- report number
- date
- status
- path

刪除 SQLite 後，應能掃描 Case 重新建立。

不要把主要案件資料只存在 SQLite。

---

## 9. 實作順序與完成條件

### Phase 1

先完成：

- 專案骨架
- 首頁
- 月曆
- 歷史案件
- GUI scale
- QSettings
- Case 基本資料模型

### Phase 2

完成：

- 人工建立 Case
- `case.json`
- Case folder
- 複製 uncertainty template

### Phase 3

完成：

- Case 頁面
- 多日量測
- `environment.json`
- `raw.csv`

### Phase 4

再加入：

- 歷史搜尋與匯入
- SQLite index
- capability
- pricing
- uncertainty engine
- report generation

### Phase 5

最後再處理：

- 預約單 OCR / Vision
- legacy Word / Excel importer
- LIMS 自動填表

### 完成條件

系統必須做到：

- 沒有歷史案件時仍可完整工作。
- 每個 Case 都能獨立保存與重現。
- template 更新不影響既有 Case。
- 自動帶入資料都可人工修改。
- uncertainty 可依案件修改。
- DUT resolution 可依案件與量程設定。
- report notes 可依案件修改。
- GUI scale 與 window state 可保存。
- E05 / E07 / E27 共用主架構，但保留各自設定與計算差異。
