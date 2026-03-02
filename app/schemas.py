from pydantic import BaseModel
from typing import List, Optional

class Question(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str # A, B, C, or D

class TestCreate(BaseModel):
    title: str
    total_time_mins: int
    questions: List[Question]