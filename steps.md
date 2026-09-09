# 校正文件管理工具實作步驟

## 1. 原則

實作時遵守：

> 如無必要勿增實體。

具體而言：

- 先完成最小可工作的流程。
- 不為尚未出現的需求預先建立 class、service、manager、database table 或抽象層。
- 能用函式、dataclass、JSON、CSV 完成，就不要增加額外框架。
- 不同功能只有在責任明確分離後才拆 module。
- 不提前加入 ORM、workflow engine、event bus、DI framework、web API、plugin system 或 background service。
- 不建立重複的 source of truth。
- `arch.md` 是架構依據；本文件只規定實作順序。

---

## 2. Step 1：建立最小專案骨架

先建立可執行的 PySide6 專案。

最低需要：

```text
main.py
src/
config/
data/
tests/
```

若目前尚無實際內容，不要先建立大量空 module 或空資料夾。

### 完成條件

執行：

```text
python main.py
```

可以正常開啟主視窗。

主視窗至少包含：

```text
月曆
歷史案件
設定
```

此階段不做案件建立、不做 OCR、不做 uncertainty、不做報告。

---

## 3. Step 2：先完成 GUI 基礎

完成 GUI 的共同規則：

- PySide6 layout manager。
- 不大量使用 absolute positioning。
- 視窗 resize 不明顯跑版。
- Windows DPI scaling 可正常使用。
- 可調整 GUI scale。
- 使用 `QSettings` 保存：
  - GUI scale
  - 主視窗大小
  - 主視窗位置

### 完成條件

關閉再開啟程式後：

- GUI scale 保留。
- 視窗大小與位置保留。
- 80%～150% scale 下主要畫面仍可正常操作。

---

## 4. Step 3：完成月曆與歷史案件入口

### 月曆

先完成：

- 切換月份。
- 點選日期。
- 顯示該日案件。
- 提供「建立新案件」入口。

此時案件可以先用簡單測試資料顯示。

### 歷史案件

先完成：

```text
E05
E07
E27
```

三個入口。

先只做列表與基本搜尋介面，不急著做完整 SQLite。

### 完成條件

使用者可以：

```text
首頁
→ 月曆
→ 日期
```

以及：

```text
首頁
→ 歷史案件
→ E05 / E07 / E27
```

順利導航。

---

## 5. Step 4：建立最小 Case model

只建立目前確定需要的 Case 資料。

至少包含：

- case ID
- system
- status
- customer
- instrument
- schedule
- previous report number
- current report number
- calibration request
- report notes

使用簡單資料模型即可，例如 dataclass。

不要先建立複雜 inheritance hierarchy。

### Case folder

建立案件時產生：

```text
cases/<year>/<system>/<case_id>/
└── case.json
```

其餘資料夾等實際需要時再建立。

### 完成條件

可以：

1. 從月曆建立新案件。
2. 在 GUI 中輸入基本資料。
3. 儲存成 `case.json`。
4. 關閉程式後重新開啟該 Case。

---

## 6. Step 5：加入系統設定

為 E05、E07、E27 建立最少必要設定。

只有真正使用到時才建立：

```text
capability.json
pricing.json
measurement_schema.json
uncertainty_template.json
```

若某個設定尚未被目前功能使用，不必先建立空檔。

### 完成條件

程式能依 Case 的 `system` 載入對應設定。

主程式不應寫死 E05 / E07 / E27 的技術規則。

---

## 7. Step 6：建立 Case-specific uncertainty

當建立 Case 時：

```text
system uncertainty template
→ copy
→ Case/uncertainty/uncertainty.json
```

實際 uncertainty 計算只讀 Case 內版本。

此階段先只完成：

- 複製
- 讀取
- 編輯
- 儲存

先不要急著完成全部 uncertainty calculation engine。

### DUT resolution

同時加入 DUT resolution 的手動輸入能力。

必須允許：

- 單一 resolution。
- 依 range 不同的 resolution。
- 之後可由歷史案件帶入。
- 使用者可覆寫。

### 完成條件

Case 建立後可以看到並修改：

```text
Case-specific uncertainty
DUT resolution
```

修改不會影響 system template。

---

## 8. Step 7：建立多日量測

Case 頁面加入：

```text
Day 1
Day 2
...
+ 新增量測日
```

每個量測日只需要：

```text
environment.json
raw.csv
```

### environment

至少支援：

- date
- operator
- temperature
- humidity
- start time
- end time
- notes

### raw data

依 `measurement_schema.json` 建立 GUI table。

GUI table 直接讀寫 CSV，不另建第二份隱藏資料格式。

### 完成條件

一個 Case 可以：

- 新增多個量測日。
- 輸入環境資料。
- 輸入 raw data。
- 儲存。
- 重新載入。

---

## 9. Step 8：建立歷史案件搜尋

等 Case 與量測格式穩定後，再加入 SQLite index。

SQLite 只保存搜尋需要的索引，例如：

- case ID
- system
- customer
- model
- serial number
- report number
- date
- status
- path

Case folder 仍是 source of truth。

### 完成條件

可以依：

- report number
- serial number
- customer
- model

找到歷史案件。

刪除 SQLite 後，可以重新掃描 Cases 建立 index。

---

## 10. Step 9：加入歷史資料匯入

找到歷史案件後，允許使用者選擇性匯入：

- customer
- instrument
- calibration points
- DUT resolution
- report notes
- previous report
- previous raw data

不得自動假設所有資料都要帶入。

所有帶入資料都必須可修改。

若使用歷史文件作參考，複製進目前 Case：

```text
reference/
```

不要只保存外部 path。

### 完成條件

即使完全沒有歷史資料，也仍可正常完成新 Case。

---

## 11. Step 10：能力驗證與報價

在 calibration points 已能正常建立後，再加入：

```text
calibration request
→ capability validation
→ pricing
```

若客戶指定「同前次報告」：

```text
previous report
→ calibration points
→ user confirmation
```

不要建立另一套獨立 workflow。

### 完成條件

使用者能看到：

- 哪些點可做。
- 哪些點超出能力。
- 預估報價。

使用者仍可修改 calibration points。

---

## 12. Step 11：Uncertainty calculation

在 raw data、DUT resolution 與 Case-specific uncertainty 都穩定後，再做完整計算。

至少支援：

- A 類。
- 系統共通 B 類。
- DUT resolution。
- Case-specific 額外 B 類。
- combined uncertainty。
- expanded uncertainty。

計算邏輯寫 Python。

JSON 只保存輸入與設定，不塞複雜公式語言。

### 完成條件

由 Case 內資料即可重新計算結果，不依賴外部 template。

---

## 13. Step 12：Report generation

最後才建立報告生成。

輸入：

```text
case.json
measurement/
processed/
uncertainty/
report notes
report template
```

輸出：

```text
report.docx
report.pdf
```

先建立正式 template，不要永久依賴「去年報告」作為 template。

### 完成條件

Case 可以由自己的資料直接產生報告。

---

## 14. Step 13：最後再做自動化輸入

核心流程穩定後，再依序考慮：

1. 預約單圖片 → OCR / Vision → 暫存 JSON。
2. legacy Excel importer。
3. legacy Word importer。
4. LIMS 自動填表。

這些都不是核心 Case workflow 的前置條件。

OCR / Vision 解析後必須先經人工確認，再正式寫入 Case。

Legacy importer 不得修改原始檔。

---

## 15. 每一步的實作規則

Codex 每完成一個 Step，都應先：

1. 執行現有 tests。
2. 啟動 GUI。
3. 驗證本 Step 的完成條件。
4. 確認沒有破壞前一 Step。
5. 再開始下一 Step。

若某功能尚未被當前 Step 使用：

> 不實作。

若某抽象只有一個使用者，而且簡單函式即可完成：

> 不新增實體。

若開始出現重複邏輯或清楚的獨立責任：

> 再考慮抽出 class 或 module。

優先確保：

```text
可以運作
→ 可以保存
→ 可以重新載入
→ 可以追溯
→ 再增加自動化
```
