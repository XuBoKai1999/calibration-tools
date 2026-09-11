# 校正文件管理工具使用手冊

## 目前可用功能

本工具是 PySide6 桌面應用程式，目前支援 E05（直流高壓）、E07（交流高壓）與 E27（片電阻）案件的建立與管理。

已實作：

- 從首頁或月曆建立案件。
- 先選擇校正系統，再選擇手動輸入或 OCR 預約單。
- 在儲存前檢查與修改 OCR 辨識結果；低信心內容不自動填入。
- 在月曆或按系統分頁的歷史清單查找、開啟已儲存案件。
- 編輯案件基本資料，並保留當前畫面未顯示的既有資料。
- 經確認後刪除單一案件。
- 調整 GUI 縮放與編輯三個系統的 JSON 設定。

## 啟動

在 repository 根目錄執行：

```powershell
python main.py
```

需先安裝 `requirements.txt` 所列的 Python dependencies。

## 建立案件

1. 選擇「建立新案件」，或在月曆選定日期後建案。
2. 選擇 E05、E07 或 E27。這個選擇會成為案件 identity，OCR 不會覆寫它。
3. 選擇「手動輸入」或「OCR 預約單」。
4. 檢查基本資料後明確儲存。儲存前不會產生正式 `case.json`。
5. 儲存後，案件會出現在月曆及正確系統的歷史清單。

如未提供本次校正點，畫面會提示需從前次報告匯入或人工確認；系統不會自行猜測。

## 案件資料位置

正式 runtime 資料位於 `data/cases/<system>/<case_id>/`；OCR 臨時資料位於 `data/staging/`，在成功建案或放棄後應被清除。`data/` 不得納入 Git。

## 設定

首頁的「設定」可調整 GUI 縮放，並檢視或編輯 E05／E07／E27 的 capability、pricing 與 measurement schema JSON。儲存時會驗證 JSON 格式、schema version、system code 與必要欄位類型。

目前這些設定內容仍是待真實歷史資料審核的 placeholder，不應自行填造 canonical 格式。

## 目前限制

- Case Workspace 的歷史資料、本次量測、不確定度與報告功能尚未實作。
- 尚未實作歷史來源選擇與 Case-local reference snapshot。
- 尚未核准 canonical raw-data format 或 `calculation.json`。
- 歷史 `past/*/source/` 檔案是唯讀原件，不可由應用程式或人工直接改寫。
