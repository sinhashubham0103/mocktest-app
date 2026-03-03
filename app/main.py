from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uuid
from .database import supabase
from .schemas import Question
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Enable CORS so your frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttemptData(BaseModel):
    test_id: str
    total_time_taken: int
    questions_attempted: int
    correct_count: int
    final_score: float
    detailed_answers: dict

@app.post("/save-attempt/")
async def save_attempt(data: AttemptData):
    # Insert the results into Supabase
    response = supabase.table("test_attempts").insert({
        "test_id": data.test_id,
        "end_time": datetime.now().isoformat(),
        "total_time_taken": data.total_time_taken,
        "questions_attempted": data.questions_attempted,
        "correct_count": data.correct_count,
        "final_score": data.final_score,
        "detailed_answers": data.detailed_answers
    }).execute()
    
    return {"message": "Attempt saved", "id": response.data[0]['id']}

@app.get("/attempts/{test_id}")
async def get_attempts(test_id: str):
    # Fetch all past attempts for a specific test
    response = supabase.table("test_attempts").select("*").eq("test_id", test_id).order("created_at", desc=True).execute()
    return response.data

@app.post("/create-test-csv/")
async def create_test_from_csv(
    title: str = Form(...), 
    duration: int = Form(...), 
    file: UploadFile = File(...)
):
    # 1. Read CSV using Pandas
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # 2. Generate a Unique Test ID
    test_id = str(uuid.uuid4())[:8] # Short unique ID for sharing
    
    # 3. Format data for Supabase
    questions_data = []
    for _, row in df.iterrows():
        questions_data.append({
            "test_id": test_id,
            "question_text": row['question'],
            "option_a": row['option_a'],
            "option_b": row['option_b'],
            "option_c": row['option_c'],
            "option_d": row['option_d'],
            "correct_option": row['correct_option']
        })
    
    # 4. Insert Test Metadata
    supabase.table("tests").insert({
        "test_id": test_id, 
        "title": title, 
        "duration_mins": duration
    }).execute()
    
    # 5. Insert Questions
    supabase.table("questions").insert(questions_data).execute()
    
    return {"message": "Test created successfully", "test_id": test_id}

@app.get("/get-test/{test_id}")
async def get_test(test_id: str):
    # Fetch test details and questions
    test_info = supabase.table("tests").select("*").eq("test_id", test_id).single().execute()
    questions = supabase.table("questions").select("*").eq("test_id", test_id).execute()
    
    if not test_info.data:
        raise HTTPException(status_code=404, detail="Test not found")
        
    return {
        "metadata": test_info.data,
        "questions": questions.data
    }