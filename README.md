# Redmine Issue Helper

這是一個協助管理與上傳 Redmine Issue 的 CLI 工具。

## 功能
- **檔案式管理**：Issue 以 YAML 格式存儲在本地，方便人工覆核與修改。
- **模板系統**：支援多個 Issue 模板（預設包含 Bug Report）。
- **自動化上傳**：依建立時間順序自動將 Pending 狀態的 Issue 上傳至 Redmine。
- **錯誤紀錄**：上傳失敗時會紀錄錯誤訊息並支援後續重試。

## 安裝說明
1. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 設定環境變數：
   複製 `.env.example` 並重新命名為 `.env`，填入您的 `REDMINE_API_KEY`。
3. 修改配置：
   編輯 `config/app.yaml` 設定 Redmine 的 `base_url` 與 `project_identifier`。

## 使用方法
### 建立新 Issue
```bash
python src/main.py create --title "標題名稱"
```
工具會引導您填寫模板定義的必要欄位。

### 查看待上傳清單
```bash
python src/main.py list
```

### 上傳至 Redmine
```bash
python src/main.py upload
```

## 目錄結構
- `config/`: 設定檔與模板。
- `issues/pending/`: 待上傳的 Issue。
- `issues/uploaded/`: 已成功上傳的 Issue 紀錄。
- `logs/`: 系統日誌。
