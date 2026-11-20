# 茶飲連鎖門市管理系統

## 專案簡介
本專案使用 Docker、Flask 和 PostgreSQL 建立茶飲連鎖門市管理系統，提供多門市資料管理及使用者登入功能。

## 使用技術
- Python Flask
- PostgreSQL
- Docker
- Docker Compose
- HTML
- JWT

## 安裝與執行方式

### 1. 下載專案
```bash
git clone https://github.com/jinx1710/teachain1120.git
cd teachain1120
```

### 2. 設定環境變數

在專案根目錄建立 `.env` 檔案：

```env
JWT_SECRET_KEY=your-secret-key
```

### 3. 啟動系統
```bash
docker compose up -d --build
```

### 4. 查看容器狀態
```bash
docker compose ps
```

### 5. 測試系統
```bash
curl http://localhost:5000/api/health
```

## 目前功能
- 使用者登入
- JWT 身分驗證
- PostgreSQL 資料庫
- 門市及商品資料管理
- Docker 容器化部署

## GitHub
https://github.com/jinx1710/teachain1120