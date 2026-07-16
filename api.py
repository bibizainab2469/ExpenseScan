from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from extractor import extract_expense
from database import insert_expense, get_all_expenses
from audit import log_entry
from extractor import extract_expense, query_expenses, save_to_chroma

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Endpoints
@app.post("/expenses/extract")
def extract(request: ExtractRequest):
    try:
        result = extract_expense(request.content)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/expenses/add")
@app.post("/expenses/add")
def add_expense(request: AddRequest):
    try:
        insert_expense(request.date, request.amount, request.category, request.description)
        save_to_chroma(
            f"Date: {request.date}. Amount: {request.amount}. Category: {request.category}. Description: {request.description}",
            {"date": request.date, "amount": request.amount, "category": request.category}
        )
        log_entry("EXPENSE_ADDED", request.dict())
        return {"success": True, "data": request.dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/expenses")
def get_expenses():
    try:
        expenses = get_all_expenses()
        return {"success": True, "data": expenses}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/expenses/query")
def query(request: QueryRequest):
    try:
        answer = query_expenses(request.question)
        return {"success": True, "data": {"answer": answer}}
    except Exception as e:
        return {"success": False, "error": str(e)}