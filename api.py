from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from database import insert_expense, get_all_expenses, get_filtered_expenses_db, get_category_breakdown, get_monthly_totals
from audit import log_entry
from extractor import extract_expense, query_expenses, save_to_chroma, extract_from_voice, extract_from_image
from fastapi.responses import FileResponse
from exporter import get_filtered_expenses, generate_excel, generate_pdf
from models import AddRequest, QueryRequest, ExtractRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints
@app.get("/")
def health_check():
    return {"success": True, "message": "Kharcha API is running"}

@app.post("/expenses/extract")
async def extract(
    input_type: str = Form(...),
    content: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        if input_type == "text":
            result = extract_expense(content)
        elif input_type == "image":
            file_bytes = await file.read()
            result = extract_from_image(file_bytes)
        elif input_type == "voice":
            file_bytes = await file.read()
            result = extract_from_voice(file_bytes, file.filename)
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}

@app.post("/expenses/add")
def add_expense(request: AddRequest):
    try:
        insert_expense(request.date, request.amount, request.category, request.vendor, request.description, request.input_type)
        try:
            save_to_chroma(
                f"Date: {request.date}. Amount: {request.amount}. Category: {request.category}. Vendor: {request.vendor}. Description: {request.description}",
                {"date": request.date, "amount": request.amount, "category": request.category}
            )
        except Exception as chroma_error:
            print(f"ChromaDB save failed: {chroma_error}")
        log_entry("EXPENSE_ADDED", request.dict())
        return {"success": True, "data": request.dict()}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": "Could not save expense. Please try again."}


@app.get("/expenses")
def get_expenses(view: str = None, date: str = None, month: str = None, year: str = None):
    try:
        if view:
            expenses = get_filtered_expenses_db(view=view, date=date, month=month, year=year)
        else:
            expenses = get_all_expenses()
        
        total = sum(e["amount"] for e in expenses)
        return {"success": True, "data": {"expenses": expenses, "total": total}}
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}

@app.post("/expenses/query")
def query(request: QueryRequest):
    try:
        answer = query_expenses(request.question)
        return {"success": True, "data": {"answer": answer}}
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}
        
@app.get("/expenses/analysis")
def get_analysis(month: str = None, year: str = None):
    try:
        categories = get_category_breakdown(month=month, year=year)
        monthly = get_monthly_totals(year=year)
        
        total = sum(c["total"] for c in categories)
        
        category_breakdown = [
            {
                "category": c["category"],
                "amount": c["total"],
                "percentage": round((c["total"] / total * 100), 1) if total > 0 else 0
            }
            for c in categories
        ]
        
        return {
            "success": True,
            "data": {
                "category_breakdown": category_breakdown,
                "monthly_totals": monthly,
                "total": total
            }
        }
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}
        
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
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}
    
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
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}