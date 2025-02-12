# FastAPI Audio Transcription API

## Description
This FastAPI-based API allows users to upload audio files, transcribe them using the Gemini API, and download the transcriptions. It supports authentication via a passphrase.

## Features
- Upload audio files (`.mp3`, `.m4a`) up to 19MB
- Transcribe audio into the original language and English
- Download transcriptions
- Secure access via passphrase authentication

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Gary0302/transcript_backend_server
   cd transcript_backend_server
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add:
   ```env
   GEMINI_API_KEY=<your_gemini_api_key>
   PASSPHRASE=<your_passphrase>
   ```
4. Run the server:
   ```sh
   uvicorn main:app --reload
   ```

## API Endpoints

### Authentication
`POST /api/authenticate`
- **Request:** `passphrase` (form data)
- **Response:** `{ "status": "authenticated" }`

### Upload Audio
`POST /api/upload`
- **Headers:** `passphrase`
- **Request:** File upload (`.mp3`, `.m4a`)
- **Response:** `{ "filename": "<uploaded_file>", "size": <size>, "status": "uploaded" }`

### Transcribe Audio
`POST /api/transcribe`
- **Headers:** `passphrase`
- **Request:** `{ "filename": "<uploaded_file>", "include_timestamps": true/false }`
- **Response:** `{ "transcript": { "original": "...", "english": "..." }, "transcript_file": "<filename>" }`

### Download Transcript
`GET /api/download/{transcript_filename}`
- **Headers:** `passphrase`
- **Response:** JSON content of the transcript

---

# FastAPI 音訊轉錄 API

## 描述
此 FastAPI API 允許用戶上傳音訊檔案，透過 Gemini API 轉錄，並下載轉錄結果。使用密碼短語進行身份驗證。

## 功能
- 上傳音訊檔案（支援 `.mp3`, `.m4a`，最大 20MB）
- 轉錄音訊為原始語言與英文
- 下載轉錄結果
- 使用密碼短語保護 API 存取

## 安裝
1. 複製儲存庫：
   ```sh
   git clone https://github.com/Gary0302/transcript_backend_server
   cd transcript_backend_server
   ```
2. 安裝依賴：
   ```sh
   pip install -r requirements.txt
   ```
3. 建立 `.env` 檔案並新增：
   ```env
   GEMINI_API_KEY=<你的 Gemini API 金鑰>
   PASSPHRASE=<你的密碼短語>
   ```
4. 啟動伺服器：
   ```sh
   uvicorn main:app --reload
   ```

## API 端點

### 身份驗證
`POST /api/authenticate`
- **請求:** `passphrase`（表單數據）
- **回應:** `{ "status": "authenticated" }`

### 上傳音訊
`POST /api/upload`
- **標頭:** `passphrase`
- **請求:** 上傳檔案（`.mp3`, `.m4a`）
- **回應:** `{ "filename": "<uploaded_file>", "size": <size>, "status": "uploaded" }`

### 轉錄音訊
`POST /api/transcribe`
- **標頭:** `passphrase`
- **請求:** `{ "filename": "<uploaded_file>", "include_timestamps": true/false }`
- **回應:** `{ "transcript": { "original": "...", "english": "..." }, "transcript_file": "<filename>" }`

### 下載轉錄內容
`GET /api/download/{transcript_filename}`
- **標頭:** `passphrase`
- **回應:** JSON 格式的轉錄內容

