from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json
from datetime import date
from dotenv import load_dotenv
import os

today = date.today().strftime("%Y-%m-%d")
load_dotenv()
key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    api_key=key,
    model="llama-3.1-8b-instant"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract expense details from user message and return ONLY a JSON object with these fields:
    - amount (number)
    - category (Food/Transport/Shopping/Health/Entertainment/Other)
    - description (brief)
    - date (today if not mentioned, format YYYY-MM-DD)
    - If no specific date is mentioned, use today's date: {{today}}
    Return ONLY the JSON. No explanation."""),
    ("human", "{text}")
])

chain = prompt | llm

def extract_expense(text):
    result = chain.invoke({"text": text, "today": today})
    data = json.loads(result.content)
    if "date" not in data or not data["date"]:
        data["date"] = today
    return data

# Test it
#test = "i had a night out with friends, ordered pizza for 900rs"
#print(extract_expense(test))