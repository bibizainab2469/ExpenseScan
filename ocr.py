from groq import Groq
from dotenv import load_dotenv
import os, base64, json
from datetime import date

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
today = date.today().strftime("%Y-%m-%d")


def extract_from_image(file_bytes):
    base64_image = base64.b64encode(file_bytes).decode('utf-8')
    
    response = groq_client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f"""Extract expense details from this receipt image and return ONLY a JSON object:
                            - amount (number only)
                            - category (must be exactly one of: Food/Transport/Shopping/Health/Entertainment/Materials/Labor/Utilities/Medical/Other)
                            - vendor (shop or person name)
                            - description (brief)
                            - date (MUST be in YYYY-MM-DD format. Today is {today}. If no date visible use today.)
                            - confidence (object with keys: amount, category, vendor, date, description — each value must be "high", "medium", or "low")
                            Return ONLY valid JSON. No explanation. No markdown."""
                    }
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Clean markdown if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())
