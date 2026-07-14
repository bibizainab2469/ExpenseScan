import chromadb

client = chromadb.Client()
collection = client.create_collection("expenses")

# Step 1: Take input
expense = input("Enter your expense: ")

# Step 2: Store it
collection.add(
    documents=[expense],
    ids=["1"]
)
print("Stored!")

# Step 3: Query
query = input("Ask about your expenses: ")
results = collection.query(query_texts=[query], n_results=1)
print(results)