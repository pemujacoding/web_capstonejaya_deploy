from groq import Groq
import os

def speech_to_text(audio_bytes, audio_name,question):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)

    transcription = client.audio.transcriptions.create(
        file=(audio_name, audio_bytes),
        model="whisper-large-v3",
        response_format="json",
        language="en"
    )

    result_stt = {
        'Question' : question,
        'Answer' : transcription.text
    }
    return result_stt