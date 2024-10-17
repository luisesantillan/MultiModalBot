from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv()

context = [
    {"role":"system","content":"Respond to the user in a casual and easy manner. Always prefix the media type of your response, for example: [a]This is my message as an audio. [v]This is my message as a video. [i]Description of the image. [t]This is my message as a text."}
    ]
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(messages:list,model="gpt-4o-mini") -> str:
    print("Getting response from OpenAI...")
    response = client.chat.completions.create(
        model=model,
        messages=context+messages,
    )
    print(f"Response received from OpenAI: {response.choices[0].message.content}")
    return response.choices[0].message.content

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