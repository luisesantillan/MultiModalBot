from telebot import TeleBot, util
from responses import get_openai_response, describe_image, text_to_speech, speech_to_text, get_gemini_response
from memory import MemoryManager
from dotenv import load_dotenv
import os
from argparse import ArgumentParser
import base64
import requests
import re
from datetime import datetime
load_dotenv()

llm = 'gemini-1.5-flash'
argparser = ArgumentParser(description='Telegram Bot')
argparser.add_argument('--clear',action='store_true', help='Clear history', default=False)
args = argparser.parse_args()
clear = args.clear
user_context = ""
bot = TeleBot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
manager = MemoryManager(clear=clear)

def get_context(extra_context:str='') -> list:
    now = datetime.now()
    date = now.strftime("%B %d, %Y")
    time = now.strftime("%I:%M %p")
    context = [
        {"role":"system","content":f"{date}. {time}. {extra_context}. You are on Telegram. You always do what the user asks. Respond to the user in a casual and easy manner. Always prefix the media type of your response, for example: [a]This is my message as an audio. [v]This is my message as a video. [i]Description of the image. [t]This is my message as a text."}
        ]
    return context

@bot.message_handler(commands=['start'])
def start(message):
    manager.clear()

@bot.message_handler(commands=['speak'])
def speak(message):
    text_to_speech(message.text.replace('/speak ', ''))
    with open('speech.mp3', 'rb') as f:
        bot.send_voice(message.chat.id, f)

@bot.message_handler(commands=['model'])
def change_model(message):
    global llm
    llm = message.text.replace('/model ', '')
    if llm == 'default' or llm == 'gemini':
        llm = 'gemini-1.5-flash'
    elif llm == "openai":
        llm = 'gpt-4o-mini'
    print(f'Model changed to "{llm}".')

@bot.message_handler(commands=['context'])
def context(message):
    global user_context
    user_context = message.text.replace('/context ', '')
    print(f'Context updated to: {message.text.replace("/context ", "")}')

@bot.message_handler(content_types=['text', 'sticker', 'pinned_message', 'photo', 'audio','voice'])
def handle_message(message):
    print(f'Received message.')
    text = ''
    if message.photo is not None:
        print('Image found in message.')
        image_path = bot.get_file(message.photo[-1].file_id).file_path
        download_path = bot.download_file(image_path)
        encoded_image = base64.b64encode(download_path).decode('utf-8')
        caption = describe_image(encoded_image)
        text += f'\n[i]{caption}.'
        if message.caption is not None:
            print(f"Caption found in message. {message.caption}")
            text += f'\n[t]{message.caption}'
    if message.text is not None:
        print('Text found in message.')
        text += f'[t]{message.text}'
    if message.voice is not None:
        print('Voice found in message.')
        downloaded_voice = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        with open('user_voice.mp3', 'wb') as speech:
            speech.write(downloaded_voice)
        speech_object = open('user_voice.mp3', 'rb')
        text += f'[a]{speech_to_text(speech_object)}'
    if text == '':
        print('No text found in message.')
        return
    manager.add_message({'role': 'user', 'content': text})
    if "gpt" in llm:
        response = get_openai_response(list(manager.memory),get_context(user_context),model=llm)
    else:
        response = get_gemini_response(list(manager.memory),get_context(user_context),model=llm)
    print(f"Addinng response to memory: {response}")
    manager.add_message({'role': 'assistant', 'content': response})
    split_responses = re.findall(r'\[\w\].*?(?=\[\w\]|$)', response, re.DOTALL)
    print(f"Split responses: {split_responses}")
    if len(split_responses) == 0:
        bot.send_message(message.chat.id, response)
        return
    for segment in split_responses:
        if segment == '':
            continue
        if segment.startswith('[a]'):
            text_to_speech(segment.replace('[a]','').strip())
            with open('client_voice.mp3', 'rb') as voice_note:
                bot.send_voice(message.chat.id, voice_note)
        elif segment.startswith('[i]'):
            image_url = f"https://image.pollinations.ai/prompt/{segment.replace('[i]','').replace(' ','+').strip()}"
            with open("image.png", "wb") as f:
                f.write(requests.get(image_url).content)
            with open("image.png", "rb") as f:
                try:
                    bot.send_photo(message.chat.id, f)
                except:
                    print(f"Failed to send image. {image_url}")
                    bot.send_message(message.chat.id, image_url)
        else:
            final_text = segment.replace('[t]','').strip()
            split_text = util.split_string(final_text, 1000)
            for t in split_text:
                print(f"Sending message: {t}")
                bot.send_message(message.chat.id, t)

bot.polling()