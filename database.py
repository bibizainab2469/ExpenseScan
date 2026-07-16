import sqlite3

DB_PATH = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date DATE NOT NULL,
            Category TEXT,
            Amount INTEGER NOT NULL,
            Description TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_expense(date, amount, category, description):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO expenses (Date, Amount, Category, Description) VALUES (?, ?, ?, ?)", 
                 (date, amount, category, description))
    conn.commit()
    conn.close()

def get_all_expenses():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM expenses")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

init_db()