from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from database import insert_expense, get_all_expenses, get_filtered_expenses_db, get_category_breakdown, get_monthly_totals, delete_expense, get_monthly_totals_for_period
from extractor import extract_expense, query_expenses, save_to_chroma
from voice import transcribe_audio
from ocr import extract_from_image
from fastapi.responses import FileResponse
from exporter import get_filtered_expenses, generate_excel, generate_pdf
from models import AddRequest, QueryRequest, ExtractRequest
from datetime import datetime, timedelta

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
            text = transcribe_audio(file_bytes, file.filename)
            result = extract_expense(text)
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}

@app.post("/expenses/add")
def add_expense(request: AddRequest):
    try:
        expense_id = insert_expense(request.date, request.amount, request.category, request.vendor, request.description, request.input_type)
        try:
            save_to_chroma(
                f"Date: {request.date}. Amount: {request.amount}. Category: {request.category}. Vendor: {request.vendor}. Description: {request.description}",
                {"date": request.date, "amount": request.amount, "category": request.category}
            )
        except Exception as chroma_error:
            print(f"ChromaDB save failed: {chroma_error}")
            delete_expense(expense_id)
            return {"success": False, "error": "Could not save expense. Please try again."}
        return {"success": True, "data": {"id": expense_id, "date": request.date, "amount": request.amount, "category": request.category, "vendor": request.vendor, "description": request.description, "input_type": request.input_type}}
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

        # --- NEW: Different response per view ---
        if view == "monthly" and month and year:
            month_name = datetime.strptime(str(month).zfill(2), "%m").strftime("%B")
            return {"success": True, "data": {
                "period": f"{month_name} {year}",
                "total_expense": total,
                "total_income": 0,
                "expenses": expenses
            }}
        elif view == "yearly" and year:
            monthly_data = get_monthly_totals(year=year)
            months = []
            for m in monthly_data:
                month_name = datetime.strptime(m["month"], "%m").strftime("%B")
                months.append({
                    "month": f"{month_name} {m['year']}",
                    "total_expense": m["total"],
                    "total_income": 0,
                    "savings": 0 - m["total"]
                })
            return {"success": True, "data": {
                "year": int(year),
                "months": months
            }}
        else:
            # daily, weekly, or no view — keep original format
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
def get_analysis(period: str = "last6months", salary: float = None):
    try:
        # Map period to start date
        today = datetime.now()
        if period == "last12months":
            start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")
        elif period == "thisyear":
            start_date = f"{today.year}-01-01"
        else:  # last6months (default)
            start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")

        categories = get_category_breakdown()  # all categories
        monthly_raw = get_monthly_totals_for_period(start_date)

        total = sum(c["total"] for c in categories)

        # Format monthly_totals as "Aug 2024" + "expense" key
        monthly_totals = []
        for m in monthly_raw:
            month_name = datetime.strptime(m["month"], "%m").strftime("%b")
            monthly_totals.append({
                "month": f"{month_name} {m['year']}",
                "expense": m["total"]
            })

        # income_vs_expense
        income_vs_expense = None
        if salary is not None:
            total_expense = sum(m["expense"] for m in monthly_totals)
            income_vs_expense = {
                "income": salary,
                "expense": total_expense,
                "savings": salary - total_expense
            }

        return {
            "success": True,
            "data": {
                "category_breakdown": categories,
                "monthly_totals": monthly_totals,
                "income_vs_expense": income_vs_expense
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
def export_pdf(period: str = "all", filename: str = "kharcha_export"):
    try:
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")

        if period == "today":
            expenses = get_filtered_expenses(date=today)
        elif period == "thismonth":
            month = datetime.now().month
            year = datetime.now().year
            expenses = get_filtered_expenses(month=month, year=year)
        else:  # all
            expenses = get_filtered_expenses()

        output_file = generate_pdf(expenses, filename=f"{filename}.pdf")
        return FileResponse(output_file, media_type="application/pdf", filename=f"{filename}.pdf")
    except Exception as e:
        print(f"Error: {e}")  # logs to your console only
        return {"success": False, "error": "Something went wrong. Please try again."}