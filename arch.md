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

### 2.1 資料責任

歷史 raw workbook 不再被視為可重建完整 Case 的權威來源。各層責任如下：

```text
Reservation / Case JSON
    customer、DUT、request-specific data

Measurement / RAW
    actual observations，以及解讀 observation 必需的 section/run/setup 語意

System Revision
    有效期間內的 standards/references、證書快照、程序、計算／不確定度及報告規則

Derived
    由 Measurement + Case + System Revision 重算的結果

Report
    依 system／measurement section／template 有條件地呈現上述資料
```

Report 是 output view，不是 canonical data store。Case JSON 仍是 Case-specific structured data 的 source of truth；同一資料不另建 report metadata database。

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

Case 描述「這個 customer、DUT 與 calibration request」：Case/work-order ID、reservation/customer reference、DUT identity、requested services/sections、optional customer accessory 與 Case notes。它不保存 laboratory-wide standards 或固定 uncertainty rules，也不要求建案時具備所有可能的 report fields；section-specific 必填條件延後到實際產報告時判定。

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

Runtime data 固定放在 repository-local `data/`，方便人工檢查，但整個目錄由 Git ignore，不屬於 version-controlled source。程式碼、設定與文件才進版控。

```text
<repo>/data/
├── staging/
├── cases/
│   ├── E05/<case_id>/
│   ├── E07/<case_id>/
│   └── E27/<case_id>/
└── index/                 # 真正建立索引時才出現
```

- `cases/`：本 application 正式管理的校正案件。
- `staging/`：OCR 臨時工作資料；成功建案或放棄後清除，不是正式 Case 資料。
- `past/<system>/source/`：application 出現以前的歷史原始材料；位於 runtime `data/` 之外，且永遠唯讀。
- `past/<system>/clean/`：只放依 `past/canonical-format.md` 產生且經人工驗證的 canonical historical packages；在代表樣本 cleaner 完成驗證前不得批次填入。
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

歷史 canonical record 已核定為一筆一目錄：

```text
past/<system>/clean/<reference_id>/
├── manifest.json          # 必有；來源、hash、generation、mapping、conflict、unresolved
├── raw.csv                # 有 observation 時才有；一個 observation 一列
├── context.csv            # 有 Case/run/range/setup/instrument context 時才有
└── report.docx            # 有合適來源或核准轉換時才有
```

`raw.csv` 以 `run_id`、`point_id`、`repeat_index` 保留量測層級；必要時加 `setup_id`、`mode`、`date`。歷史清理只從 raw workbook 擷取不可替代的 observation，以及解讀 observation 必需的最小 section/run/setup 語意。不得因 Excel 中存在 customer/DUT、完整 instrument inventory、追溯表、固定 uncertainty、helper、prior result 或 report-layout 資料，就擴張 raw parser 以重建完整 Case。

`context.csv` 固定為 scoped long form：`scope_type,scope_id,key,value,unit,note,source`，但它是 canonical package 的承載能力，不代表所有 context 都應由 raw workbook 取得。未來如需歷史 Case/report reconstruction，應先依最低 report variables，從可信 Case/reservation 或小型 report parser 補入必要資料。E05、E07、E27 的 RAW 欄位依各自 `clean-schema.md` 定義，不建立萬用 schema。缺少 raw/context/report 合法，並由 manifest 明記；未知 measurement 語意必須 fail／unresolved，不以成功率換取 silent data loss。

完整 cross-system invariant 與 system schema 分別見 `past/canonical-format.md`、`past/E05/clean-schema.md`、`past/E07/clean-schema.md`、`past/E27/clean-schema.md`。

來源可為前一個 managed Case，或 `past/<system>/source/` 中的 legacy item。使用者選定後，raw data 與 report 必須複製到當前 Case，不能只記外部路徑：

```text
historical source
      ↓ copy
current Case/reference/
```

Case-local `reference/` 是該案件實際採用的 immutable snapshot；`past/*/source/` 是唯讀 archive/source。不得原地修改兩者內的檔案。沒有歷史材料時 Case 仍須可用，且建立後也能稍後選擇 reference。不另建重複的 global `data/references/` archive。

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

上述現有 config layout 不等於未來 revision 檔案設計。未來 Case／measurement execution 必須綁定一個 controlled System Revision；revision 有明確有效期間、可在年中變更，且 Settings 後續修改不得改寫既有 Case。它概念上擁有可用 standards/references、序號與 certificate snapshot/value/uncertainty、applicability/range rules、procedure/evaluation revision、calculation/uncertainty/coverage/conversion/correction rules，以及 report-template revision 與固定 wording。現在不先設計 revision JSON。

System Revision 擁有「可用標準與選用規則」；measurement execution 依 method/range 解決並記錄實際使用的標準。正常 Case 不要求使用者逐筆手輸 standard ID，實際使用結果仍須可稽核。E27 五顆 standard resistor 是 revision inventory，每案只記錄實際選用的一顆。

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

Derived values 由 Measurement + Case + bound System Revision 重算；mean、conversion、ratio/phase result、correction、Type A、combined/expanded uncertainty 與 report result table 不因出現在報告中就成為 Case input。

一個 Case/report 可包含一個或多個 measurement sections，例如 DC high voltage、AC high voltage、voltage-transformer ratio/phase 或 AC voltage transfer。section 是資料概念，不新增 manager/workflow framework；每個 section 決定自己的 observation/setup 與 report-required fields。

產生報告時採 conditional field resolution：

```text
selected report template / sections
→ required variables
→ Case JSON / reservation-derived Case data
→ measurement data / context
→ bound System Revision
→ derived result
→ 仍缺少時才提示使用者提供或確認
```

使用者不必在建案時填完所有可能欄位。E05 customer meter、E07 ratio/excitation/burden/frequency、E27 conductivity/orientation/diameter/thickness 等，只在適用 section/template 中成為必填。經確認的 Case-specific 缺值可在未來寫回 Case JSON；不另建 report metadata database。

Reservation/intake 是 customer、contact、recipient、DUT identity、requested service/points、special requirements 與 planned date 的優先來源。已有 Case/reservation data 時，不回頭以 dirty historical raw Excel 作主要來源。

前次 report 永不直接修改：

```text
case/reference/report.docx
→ copy
case/report/<current-report>.docx
→ 修改 current copy
```

reference report 可供比較，但不作 current report 的 canonical data source。報告 template/section 定義其變數需求；current report 由 Case、Measurement、System Revision 與 Derived 組成。新 DUT 沒有前次 report 時仍可產報告；現階段允許用外部程式開啟 DOCX，不要求內嵌 Word viewer/editor。

歷史 report parser 若後續證明必要，只回收 application/template 真正需要而其他來源缺少的 Case metadata，例如 DUT/report metadata、customer accessory、E27 material/geometry 或特殊 notes；不建立通用 Word parser，也不重建固定 prose。

## 10. 實作狀態

### 已實作

- 薄 `main.py`、主要 GUI pages、navigation、GUI scale 與 QSettings。
- Case model/storage/service、人工與 OCR 基本資料建案。
- OCR confidence filtering 與 staging cleanup。
- Case non-destructive GUI update、schema-version 與未知頂層欄位保護。
- E05/E07/E27 基本 config 載入、編輯與最低語意驗證。
- runtime `data/` 固定在 repository 內供人工檢查，並由 Git 完整忽略。
- 先選 system 的 manual/OCR New Case flow 與 Case Workspace shell。
- Case 路徑 `cases/<system>/<case_id>/`、舊年度路徑安全移轉及單一 Case 刪除。
- persisted Case 儲存後立即更新 Calendar／History，並可重新開啟。

### 穩定目標但尚未完成

- historical source selection 與 Case-local reference snapshot。
- canonical measurement format、measurement workspace、calculation、uncertainty 與 report generation。
- `calculation.json`。
