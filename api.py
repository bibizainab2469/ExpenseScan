from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import insert_expense, get_all_expenses
from audit import log_entry
from extractor import extract_expense, query_expenses, save_to_chroma, extract_from_voice
from fastapi.responses import FileResponse
from exporter import get_filtered_expenses, generate_excel, generate_pdf
import asyncio

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
from fastapi import File, UploadFile, Form
import os

@app.post("/expenses/extract")
async def extract(
    input_type: str = Form(...),
    content: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        if input_type == "text":
            result = extract_expense(content)
        elif input_type == "voice":
            file_bytes = await file.read()
            result = extract_from_voice(file_bytes, file.filename)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    
@app.get("/expenses/export/excel")
def export_excel(
    month: str = None, 
    year: str = None, 
    category: str = None,
    filename: str = "kharcha_export"
):
    try:
        expenses = get_filtered_expenses(month=month, year=year, category=category)
        output_file = generate_excel(expenses, filename=f"{filename}.xlsx")
        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{filename}.xlsx"
        )
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@app.get("/expenses/export/pdf")
def export_pdf(month: str = None, year: str = None, category: str = None, filename: str = "kharcha_export"):
    try:
        expenses = get_filtered_expenses(month=month, year=year, category=category)
        output_file = generate_pdf(expenses, filename=f"{filename}.pdf")
        return FileResponse(
            output_file,
            media_type="application/pdf",
            filename=f"{filename}.pdf"
        )
    except Exception as e:
        return {"success": False, "error": str(e)}