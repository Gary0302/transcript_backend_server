from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import aiofiles
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://transcription-app-mu.vercel.app"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Constants
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".mp3", ".m4a"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
PASSPHRASE = os.getenv("PASSPHRASE")

# Create upload directory if it doesn't exist
# 原本的 UPLOAD_DIR = "uploads"
UPLOAD_DIR = "/tmp/uploads"  # 使用 /tmp 目錄確保可寫入
os.makedirs(UPLOAD_DIR, exist_ok=True)


class TranscriptionRequest(BaseModel):
    filename: str
    include_timestamps: bool

@app.get("/")
async def index():
    return {"message": "function ready"}

@app.post("/api/authenticate")
async def authenticate(passphrase: str = Form(...)):
    if passphrase != PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid passphrase")
    return {"status": "authenticated"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    passphrase: str = Header(None)
):
    # Verify passphrase
    if passphrase != PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid passphrase")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Read file content and check size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
            
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "filename": unique_filename,
        "size": len(file_content),
        "status": "uploaded"
    }

@app.post("/api/transcribe")
async def transcribe_audio(
    request: TranscriptionRequest,
    passphrase: str = Header(None)
):
    # Verify passphrase
    if passphrase != PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid passphrase")
    
    file_path = os.path.join(UPLOAD_DIR, request.filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Read file as bytes
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Determine MIME type based on file extension
        file_ext = os.path.splitext(request.filename)[1].lower()
        
        # 使用正確的標準 MIME 類型
        if file_ext == '.mp3':
            mime_type = 'audio/mpeg'  # 正確的 MP3 MIME 類型
        elif file_ext == '.m4a':
            mime_type = 'audio/x-m4a'  # 適用於 M4A 的 MIME 類型
        else:
            # 預設情況
            mime_type = 'audio/mpeg'
        
        print(f"Processing file: {file_path}, Extension: {file_ext}, MIME type: {mime_type}")
        # Create prompts for both languages
        timestamp_format = "[MM:SS]" if request.include_timestamps else ""
        prompt = f"""Please provide two transcriptions for this audio:
1. A origin transcript{timestamp_format} 
2. An English translation {timestamp_format}

Please format your response as follows:
[ORIGINAL]
(Original language transcription here)

[ENGLISH]
(English translation here)

Note1: Make sure to include line breaks between each section of the transcript, but don't be too trivial
"""

        # Generate content using Gemini
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type
                )
            ]
        )
        
        # Parse the response to separate original and English transcripts
        text = response.text
        original_text = ""
        english_text = ""
        
        # Split the response into sections
        if "[ORIGINAL]" in text and "[ENGLISH]" in text:
            parts = text.split("[ENGLISH]")
            original_text = parts[0].replace("[ORIGINAL]", "").strip()
            english_text = parts[1].strip()
        else:
            # Fallback if format is different
            english_text = text
            original_text = text

        transcript = {
            "original": original_text,
            "english": english_text,
            "timestamps": request.include_timestamps
        }
        
        # Save transcript to file
        transcript_filename = f"{os.path.splitext(request.filename)[0]}_transcript.txt"
        transcript_path = os.path.join(UPLOAD_DIR, transcript_filename)
        
        async with aiofiles.open(transcript_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(transcript, indent=2, ensure_ascii=False))
        
        # Clean up original audio file
        os.remove(file_path)
        
        return {
            "transcript": transcript,
            "transcript_file": transcript_filename
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{transcript_filename}")
async def download_transcript(
    transcript_filename: str,
    passphrase: str = Header(None)
):
    # Verify passphrase
    if passphrase != PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid passphrase")
    
    file_path = os.path.join(UPLOAD_DIR, transcript_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))