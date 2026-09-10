# 校正文件管理工具實作步驟

## 1. 實作規則

> 如無必要勿增實體。

- `arch.md` 先固定完整責任邊界；module 在功能首次出現時才建立。
- 新邏輯放到責任最直接的位置，不以 GUI callback 實作 JSON、CSV、OCR 或計算。
- 一個 module 同時承擔兩個以上明顯責任時再拆分。
- 不為 design pattern 建立沒有實際責任的 Manager、Controller、Repository、Factory 或空目錄。
- 依賴方向固定為 `GUI → feature logic → storage/config`，不得反向 import GUI。

每完成一步：

1. 執行現有 tests。
2. 實際啟動 GUI。
3. 驗證本 Step 的完成條件。
4. 確認沒有破壞前一步。
5. 確認文件、程式位置與資料位置一致。

## 2. Step 1：bootstrap 與 GUI 骨架

建立薄的 `main.py`、`gui/main_window.py` 及實際存在的 Page。`main.py` 只負責 application、data path、settings、window 與 event loop。

完成條件：`python main.py` 能開啟首頁，並可進入月曆、歷史案件與設定。

## 3. Step 2：GUI 基礎

使用 layout manager，完成 DPI、GUI scale、快捷鍵、Ctrl+滑鼠滾輪、window geometry 與 QSettings。高倍率頁面須可捲動。

完成條件：關閉重開後保留 UI state，主要頁面無明顯重疊或裁切。

## 4. Step 3：預約與 Intake

### 月曆

完成月份切換、選取日期、顯示當日案件與建立案件入口。

### 照片建案

責任流程固定為：

```text
intake/ocr.py
→ structured OCR result
→ intake/reservation.py normalize
→ data/inbox/<temporary-id>/parsed.json
→ GUI 人工確認
→ cases/service.py
```

OCR 不得建立 Case 或寫 `case.json`。人工確認以前，資料只能存在 inbox staging。

欄位解析應優先取得前次報告編號，供後續歷史案件查找；照片中不存在或無法可靠辨識的 LIMS 欄位保持空白，不以猜測補值。

完成條件：照片能產生 staging、表單可修改，且尚未按儲存時不會產生正式 Case。

## 5. Step 4：Case model、storage 與建案

- `cases/model.py`：描述 Case。
- `cases/storage.py`：Case folder、JSON load/save、複製 reservation files。
- `cases/service.py`：產生 ID、建立與確認 Case。
- `gui/pages/case_page.py`：只負責可編輯表單。

建立：

```text
data/cases/<year>/<system>/<case_id>/case.json
```

若由照片建立，確認後將 staging 中的 `original.<ext>` 與 `parsed.json` 複製到 Case `reservation/`。

完成條件：可人工或由照片建立 Case、儲存、關閉並重新開啟；GUI 不包含 JSON serialization。

## 6. Step 5：System configuration

功能首次需要時建立 `systems/loader.py`，讀取 `config/systems/<system>/`。只有 capability 與 pricing 真正使用時才建立相應 module 與 JSON。

完成條件：主程式與 GUI 不寫死 E05/E07/E27 技術規則，且沒有 E05Manager 等空殼 class。

## 7. Step 6：Case-specific uncertainty

建立 Case 時把 system uncertainty template 複製到 Case。先完成讀取、編輯與保存；完整計算仍不實作。

完成條件：Case 可修改自己的 uncertainty 與單一／分 range DUT resolution，不影響 system template。

## 8. Step 7：多日量測

功能出現時建立 `measurement/storage.py`；只有真正需要資料處理時才建立 `processing.py`。

```text
measurement/day_01/environment.json
measurement/day_01/raw.csv
```

完成條件：可新增多個量測日、保存與重新載入環境及 raw data；GUI 不自行讀寫 CSV。

## 9. Step 8：History index

Case 與量測格式穩定後建立 `history/index.py`。SQLite 只保存搜尋欄位與 Case path，Case folder 仍是 source of truth。

完成條件：可依報告編號、序號、客戶、型號搜尋；刪除 SQLite 後可重建。

## 10. Step 9：歷史資料匯入

History 只回傳找到的 Case；選擇性匯入與檔案複製由 Case service 處理。所有匯入值可修改，參考文件複製到 Case `reference/`。

完成條件：沒有歷史資料仍可完成新 Case，且匯入不依賴原案件的永久路徑。

## 11. Step 10：能力驗證與報價

建立 `systems/capability.py`、`systems/pricing.py` 及真正使用的 config。客戶指定「同前次報告」時，以歷史校正點作來源並要求確認，不另建 workflow。

完成條件：顯示可做／超出能力的校正點及預估報價，使用者仍可修改校正點。

## 12. Step 11：Uncertainty calculation

建立 `uncertainty/engine.py`，計算 A 類、系統共通 B 類、DUT resolution、每案額外 B 類、combined 與 expanded uncertainty。

完成條件：只靠 Case 內資料即可重算，不 import GUI，不把複雜公式語言塞進 JSON。

## 13. Step 12：Report generation

建立 `reports/generator.py`，由 Case、measurement、processed data、uncertainty 與正式 template 產生 DOCX/PDF。

完成條件：Case 能由自己的資料產生報告；report notes 仍保存在 Case，不另建第二份 source of truth。

## 14. Step 13：Legacy import 與外部自動化

需要時才建立 `legacy/excel.py`、`legacy/word.py`，只解析舊檔並回傳資料。Case service 決定如何 copy、normalize、save；不得修改原始檔。

最後才評估 LIMS 自動填表與其他外部整合，不讓它們成為核心 Case workflow 的前置條件。
