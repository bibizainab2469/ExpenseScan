import sqlite3


connection = sqlite3.connect("expenses.db")
cursor = connection.cursor()
    
cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Date DATE NOT NULL,
        Category TEXT,
        Amount INTEGER NOT NULL,
        Description STR
    )
""")

# 4. Save changes
connection.commit()

print("Table created successfully!")

def insert_expense(date, amount, category, description):
    cursor.execute("INSERT INTO expenses (Date, Amount, Category, Description) VALUES (?, ?, ?, ?)", (date, amount, category, description))
    connection.commit()
    
def get_all_expenses():
    cursor.execute("SELECT * FROM expenses")
    return cursor.fetchall()

print(get_all_expenses())