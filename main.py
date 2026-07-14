import chromadb

client = chromadb.Client()
collection = client.create_collection("expenses")

# Store multiple expenses
expenses = []

while True:
    print("\n1. Add expense")
    print("2. Query expenses")
    print("3. Exit")
    
    choice = input("Choose: ")
    
    if choice == "1":
        expense = input("Enter expense: ")
        id = str(len(expenses) + 1)
        collection.add(documents=[expense], ids=[id])
        expenses.append(expense)
        print("Stored!")
    
    elif choice == "2":
        query = input("Ask: ")
        results = collection.query(query_texts=[query], n_results=3)
        print("\nResults:")
        for doc in results['documents'][0]:
            print("-", doc)
    
    elif choice == "3":
        break