from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(file_bytes, filename):
    result = groq_client.audio.transcriptions.create(
        model=os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo"),
        file=(filename, file_bytes)
    )
    return result.text
