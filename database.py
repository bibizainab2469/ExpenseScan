import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
DB_PATH = os.getenv("SQLITE_DB_PATH", "./expenses.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            date DATE NOT NULL,
            category TEXT,
            amount REAL NOT NULL,
            vendor TEXT,
            description TEXT,
            input_type TEXT,
            created_at TEXT
)
    """)
    conn.commit()
    conn.close()

import uuid

def insert_expense(date, amount, category, vendor, description, input_type):
    expense_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO expenses (id, date, amount, category, vendor, description, input_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (expense_id, date, amount, category, vendor, description, input_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return expense_id
    
def get_filtered_expenses_db(view=None, date=None, month=None, year=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    
    if view == "daily" and date:
        query += " AND date = ?"
        params.append(date)
        
    elif view == "weekly" and date:
        conn2 = sqlite3.connect(DB_PATH)
        # Get the week start (Monday) and end (Sunday) for the given date
        from datetime import datetime, timedelta
        d = datetime.strptime(date, "%Y-%m-%d")
        week_start = d - timedelta(days=d.weekday())
        week_end = week_start + timedelta(days=6)
        query += " AND date BETWEEN ? AND ?"
        params.append(week_start.strftime("%Y-%m-%d"))
        params.append(week_end.strftime("%Y-%m-%d"))
    
    elif view == "monthly" and month and year:
        query += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.append(str(month).zfill(2))
        params.append(str(year))
    
    elif view == "yearly" and year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    
    query += " ORDER BY date DESC"
    
    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_category_breakdown(month=None, year=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT category, SUM(amount) as total FROM expenses WHERE 1=1"
    params = []
    
    if month and year:
        query += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.append(str(month).zfill(2))
        params.append(str(year))
    elif year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    
    query += " GROUP BY category ORDER BY total DESC"
    
    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_monthly_totals(year=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = """SELECT strftime('%m', date) as month, 
               strftime('%Y', date) as year,
               SUM(amount) as total 
               FROM expenses WHERE 1=1"""
    params = []
    
    if year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    
    query += " GROUP BY year, month ORDER BY year, month"
    
    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_all_expenses():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM expenses")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

init_db()