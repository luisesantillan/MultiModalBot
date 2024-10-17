from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text:str):
    print("Generating TTS...")
    speech_file_path = Path(__file__).parent / "client_voice.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )
    print("TTS generated.")
    response.stream_to_file(speech_file_path)
    return response.content

def speech_to_text(speech_object) -> str:
    print("Transcribing speech...")
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=speech_object
    )
    print(f"Transcription received from OpenAI: {response.text}")
    return response.text

def describe_image(encoded_image) -> str:
    print("Captioning image...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages = [
                {"role":"system","content":"Caption this image for a blind person to understand fully using tags or keywords."},
                {"role":"user","content":[
                    {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+encoded_image}}
                    ]}
                ]
        )
    print(f"Caption received from OpenAI: {response.choices[0].message.content}")
    return response.choices[0].message.content

def get_openai_response(messages:list,context:list,model:str="gpt-4o-mini") -> str:
    print("Getting response from OpenAI...")
    response = client.chat.completions.create(
        model=model,
        messages=context+messages,
    )
    print(f"Response received from OpenAI: {response.choices[0].message.content}")
    return response.choices[0].message.content

def get_gemini_response(messages:list,context:list,model:str="gemini-1.5-flash") -> str:
    if not "tuned" in model:
        gemini = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=context[0]['content']
        )
    else:
        gemini = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
        )
    formatted_messages = []
    for message in messages:
        formatted_messages.append({"role":message["role"].replace("assistant","model"),"parts":[message["content"]]})
    print(f"Messages sent to Gemini: {formatted_messages}")
    model_turn = formatted_messages[-1].get("role",None) == "user"
    print(f"Model turn: {model_turn}")
    try:
        if model_turn:
            session = gemini.start_chat(history=formatted_messages)
            response = session.send_message(formatted_messages[-1])
        else:
            response = session.start_chat(formatted_messages)
    except Exception as e:
        print(f"Error: {e}")
        return ""
    print(f"Response received from Gemini: {response.text}")
    return response.text