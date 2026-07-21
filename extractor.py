from dotenv import load_dotenv
import os
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json
from datetime import datetime, timezone, timedelta
import chromadb
import uuid

chroma_client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./expense_db"))
collection = chroma_client.get_or_create_collection("expenses")

key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    api_key=key,
    model="llama-3.1-8b-instant"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract expense details and return ONLY a JSON object:
    - amount (number only), default is pkr rupee, if not mentioned, use default
    - category (must be exactly one of: Food/Transport/Shopping/Health/Entertainment/Materials/Labor/Utilities/Medical/Other)
    - description (brief)
    - vendor (shop name or person paid, null if not mentioned)
    - date (MUST be in YYYY-MM-DD format only. Today is {today}. If no date mentioned use today.
    - confidence (object with keys: amount, category, vendor, date, description — each value must be "high", "medium", or "low"))
    
    Return ONLY valid JSON. No explanation. No markdown."""),
    ("human", "{text}")
])

chain = prompt | llm

def extract_expense(text):
    pakistan_tz = timezone(timedelta(hours=5))
    today = datetime.now(pakistan_tz).strftime("%Y-%m-%d")
    result = chain.invoke({"text": text, "today": today})
    data = json.loads(result.content)
    if "date" not in data or not data["date"]:
        data["date"] = today
    return data

def query_expenses(question):
    results = collection.query(query_texts=[question], n_results=5)
    context = "\n".join(results['documents'][0])
    
    prompt = f"""You are an expense tracking assistant.
Here are relevant expense records:
{context}

Answer this question: {question}"""
    
    response = llm.invoke(prompt)
    return response.content
# Test it
#test = "i had a night out with friends, ordered pizza for 900rs"
#print(extract_expense(test))

def save_to_chroma(expense_text, metadata):
    collection.add(
        documents=[expense_text],
        metadatas=[metadata],
        ids=[str(uuid.uuid4())]
    )
    