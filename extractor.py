from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from groq import Groq
import json
from datetime import date
from dotenv import load_dotenv
import os
import chromadb

chroma_client = chromadb.PersistentClient(path="./expense_db")
collection = chroma_client.get_or_create_collection("expenses")

today = date.today().strftime("%Y-%m-%d")
load_dotenv()
key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    api_key=key,
    model="llama-3.1-8b-instant"
)

groq_client = Groq(api_key=key)

def transcribe_audio(file_bytes, filename):
    result = groq_client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=(filename, file_bytes)
    )
    return result.text

prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract expense details and return ONLY a JSON object:
    - amount (number only)
    - category (must be exactly one of: Food/Transport/Shopping/Health/Entertainment/Materials/Labor/Utilities/Medical/Other)
    - description (brief)
    - date (MUST be in YYYY-MM-DD format only. Today is {today}. If no date mentioned use today.)
    Return ONLY valid JSON. No explanation. No markdown."""),
    ("human", "{text}")
])

chain = prompt | llm

def extract_expense(text):
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
        ids=[str(metadata.get("id", expense_text[:10]))]
    )
    
def extract_from_voice(file_bytes, filename):
    text = transcribe_audio(file_bytes, filename)
    return extract_expense(text)