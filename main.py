from extractor import extract_expense
from audit import log_entry
import chromadb

client = chromadb.PersistentClient(path="./expense_db")
collection = client.get_or_create_collection("expenses")
# Store multiple expenses
expenses = []

while True:
    print("\n1. Add expense")
    print("2. Query expenses")
    print("3. Exit")
    
    choice = input("Choose: ")
    
    if choice == "1":
        expense = input("Enter expense: ")
        structured = extract_expense(expense)
        print(f"Extracted: {structured}")
        collection.add(
            documents=[str(structured)],
            ids=[str(len(expenses) + 1)]
        )
        expenses.append(structured)
        print("Stored!")
        log_entry("EXPENSE_ADDED", structured)
    
    elif choice == "2":
        query = input("Ask: ")
        results = collection.query(query_texts=[query], n_results=3)
        print("\nResults:")
        for doc in results['documents'][0]:
            print("-", doc)
    
    elif choice == "3":
        break