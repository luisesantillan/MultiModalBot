from telebot import TeleBot, util
from responses import get_openai_response, describe_image, text_to_speech, speech_to_text, get_gemini_response, get_openai_models
from memory import MemoryManager
from dotenv import load_dotenv
import os, json,  base64, re, requests, shutil
from argparse import ArgumentParser
from datetime import datetime
load_dotenv()
settings_file = "settings.json"
try:
    with open(settings_file, "r", encoding="utf-8") as f:
        settings = json.load(f)
        llm = settings['model']
except Exception as e:
    print(e)
    llm = "gpt-4o-mini"

argparser = ArgumentParser(description='Telegram Bot')
argparser.add_argument('--clear',action='store_true', help='Clear history', default=False)
args = argparser.parse_args()
clear = args.clear
user_context = ""
bot = TeleBot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
manager = MemoryManager(clear=clear)

def get_context(change_user_context:str='') -> list:
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"Error reading settings.json: {e}")
        raise FileNotFoundError("settings.json file not found. Please ensure the settings file exists in the correct location.")
    date = datetime.now().strftime("%B %d, %Y")
    time = datetime.now().strftime("%I:%M %p")
    if change_user_context == '':
        context = [{"role":"system","content":f"{date}. {time}. {settings['user_context'][0]['content']} {settings['system_prompt']}"}]
        print(f"Context: {context}")
        return context
    context = [
        {"role":"system","content":f"{date}. {time}. {change_user_context} {settings['system_prompt']}"}
        ]
    settings['user_context'][0]['content'] = change_user_context
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    print(f"User context changed to: {change_user_context}")
    print(f"Actual context sent: {context}")
    return context

@bot.message_handler(commands=['load'])#Load custom settings.json
def load(message):
    global settings_file
    settings_file = message.text.replace('/load ', '')+'.json'
    print(f'Settings file changed to "{settings_file}". This will be used in this session.')
    if not os.path.exists(settings_file):
        print(f"Creating new settings file: {settings_file}")
        shutil.copyfile('settings.json', settings_file)

@bot.message_handler(commands=['show'])
def show(message):
    text = message.text.replace('/show', '').strip()
    print(f'Searching for "{text}"')
    if text != '':
        model = get_openai_models(text)
        print(model)
    else:
        models =  get_openai_models()
        for model in models:
            print(model)
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
    name = message.text.replace('/model ', '')
    if name == "openai":
        llm = 'gpt-4o-mini'
    elif name == "gemini":
        llm = 'gemini-1.5-flash'
    elif "gem" in name:
        llm = name
    else:
        llm = get_openai_models(name)
    print(f'Model changed to "{llm}".')
    with open(settings_file, "r", encoding="utf-8") as f:
        settings = json.load(f)
    with open(settings_file, "w", encoding="utf-8") as f:
        settings['model'] = llm
        json.dump(settings, f, indent=4)

@bot.message_handler(commands=['context'])
def context(message):
    global user_context
    user_context = message.text.replace('/context ', '')
    get_context(user_context)

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
    if not response.startswith('['):
        response = f'[t]{response}'
    split_responses = re.findall(r'\[\w\].*?(?=\[\w\]|$)', response, re.DOTALL)
    print(f"Split responses: {split_responses}")
    for segment in split_responses:
        if segment == '':
            continue
        if segment.startswith('[a]'):
            print(f"Adding audio to memory: {segment}")
            manager.add_message({'role': 'assistant', 'content': segment})
            text_to_speech(segment.replace('[a]','').strip())
            with open('client_voice.mp3', 'rb') as voice_note:
                bot.send_voice(message.chat.id, voice_note)
        elif segment.startswith('[i]'):
            image, url, prompt = get_image(segment)
            print(f"Adding image to memory: {prompt}")
            manager.add_message({'role': 'assistant', 'content': prompt})
            with open(image, "rb") as f:
                try:
                    bot.send_photo(message.chat.id, f)
                except:
                    print(f"Failed to send image. {url}")
        else:
            split_text = util.split_string(segment.strip(), 1000)
            for t in split_text:
                print(f"Adding text to memory: {t}")
                manager.add_message({'role': 'assistant', 'content': t})
                cleaned_text = t.replace('[t]','').strip()
                bot.send_message(message.chat.id, cleaned_text)

def get_image(text):
    with open('settings.json', 'r') as f:
        settings = json.load(f)
    text = text.replace('[i]','').strip()
    messages = [
        {"role": "system", "content": settings['text_to_image_system_prompt']},
        {"role": "user", "content": f"{settings['text_to_image_user_prompt']} {text}"}
    ]
    response = get_openai_response(messages,model='ft:gpt-3.5-turbo-1106:rejekts:minovia100x2:98KbVqaT',temperature=0.5)
    print(f"Generated prompt: {response}")
    image_url = f"https://image.pollinations.ai/prompt/{response.replace(' ','+').strip()}"
    with open("image.png", "wb") as f:
        f.write(requests.get(image_url).content)
    return "image.png", image_url, response

bot.polling()