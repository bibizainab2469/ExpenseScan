from pydantic import BaseModel
from typing import Optional

# Models
class ExtractRequest(BaseModel):
    input_type: str
    content: str

class AddRequest(BaseModel):
    date: str
    amount: float
    category: str
    vendor: Optional[str] = None
    description: Optional[str] = None
    input_type: str

class QueryRequest(BaseModel):
    question: str