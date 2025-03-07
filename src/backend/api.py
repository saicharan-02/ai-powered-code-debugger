import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import ast
import pylint.lint
import autopep8
from .code_analyzer import CodeAnalyzer
from .ai_service import AIService

# Load environment variables
load_dotenv()

# Get configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="AI Code Debugger API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
code_analyzer = CodeAnalyzer()
ai_service = AIService()

class CodeRequest(BaseModel):
    code: str
    filename: Optional[str] = None

class DebugResponse(BaseModel):
    errors: List[Dict]
    suggestions: List[Dict]
    performance_tips: List[Dict]
    formatted_code: str

@app.post("/analyze", response_model=DebugResponse)
async def analyze_code(code_request: CodeRequest):
    try:
        # Analyze code for errors and suggestions
        errors = code_analyzer.find_errors(code_request.code)
        suggestions = await ai_service.get_suggestions(code_request.code, errors)
        performance_tips = code_analyzer.analyze_performance(code_request.code)
        formatted_code = autopep8.fix_code(code_request.code)

        return DebugResponse(
            errors=errors,
            suggestions=suggestions,
            performance_tips=performance_tips,
            formatted_code=formatted_code
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        code = contents.decode("utf-8")
        return await analyze_code(CodeRequest(code=code, filename=file.filename))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str
    code_context: str

@app.post("/chat")
async def chat_with_ai(chat_request: ChatRequest):
    try:
        response = await ai_service.get_chat_response(
            chat_request.message,
            chat_request.code_context
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT) 