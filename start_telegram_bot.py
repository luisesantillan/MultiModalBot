from telebot import TeleBot, util
from utils import describe_image, text_to_speech, speech_to_text, get_gemini_response, get_openai_models
from memory import MemoryManager
from dotenv import load_dotenv
import os, json,  base64, requests, shutil
from argparse import ArgumentParser
from datetime import datetime
from swarm import Swarm, Agent
load_dotenv()
swarm = Swarm(os.getenv("OPENAI_API_KEY"))
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
        try:
            llm = get_openai_models(name)
        except Exception as e:
            print(e)
            print(f'Model "{name}" not found. Using default model.')
            llm = 'gpt-4o-mini'
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
        text += f'\n[Image Sent. Content:]{caption}[End]'
        if message.caption is not None:
            print(f"Caption found in message. {message.caption}")
            text += f'\n[t]{message.caption}'
    if message.text is not None:
        print('Text found in message.')
        text += f'\n{message.text}'
    if message.voice is not None:
        print('Voice found in message.')
        downloaded_voice = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        with open('user_voice.mp3', 'wb') as speech:
            speech.write(downloaded_voice)
        speech_object = open('user_voice.mp3', 'rb')
        text += f'\n[Audio Sent. Content:]{speech_to_text(speech_object)}[End]'
    if text == '':
        print('No text found in message.')
        return
    manager.add_message({'role': 'user', 'content': text.strip()})
    if "gpt" in llm:
        response = get_openai_response(list(manager.memory),get_context(user_context),model=llm,id=message.chat.id)
    else:
        response = get_gemini_response(list(manager.memory),get_context(user_context),model=llm)
    split_text = util.split_string(response.strip(), 1000)
    for t in split_text:
        print(f"Adding text to memory: {t}")
        manager.add_message({'role': 'assistant', 'content': t})
        bot.send_message(message.chat.id, t)

def get_openai_response(messages:list,context:list=[],model:str="gpt-4o-mini",temperature=0.5,id=None) -> str:
    print("Getting response from OpenAI...")
    response = swarm.run(
        agent=Agent(model=model,temperature=temperature,functions=[send_image,send_audio]),
        messages=context+messages,
        context_variables={"chat_id":id}
    )
    print(f"Response received from OpenAI: {response.messages[-1]['content']}")
    return response.messages[-1]['content']

def send_image(context_variables, prompt):
    f"""{settings["text_to_image_system_prompt"]}{settings["text_to_image_user_prompt"]}
    Args:
        prompt: Detailed descriptio for an image using keywords
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','+').strip()}"
    filename = f"{timestamp}.png"
    with open(filename, "wb") as f:
        try:
            f.write(requests.get(image_url).content)
        except Exception as e:
            print(f"Error: {e}")
            return {"result":"Error: Failed to send image.","filename":""}
    with open(filename,"rb") as f:
        bot.send_photo(context_variables['chat_id'],f)
        print(f"Prompt: {prompt}")
        manager.add_message({"role":"assistant","content":f"[Image Sent. Caption:]{prompt}[End]"})
    return {"result":"Image sent!","filename":filename}

def send_audio(context_variables, speech):
    f"""Say anything you want and this will speak for you.
    Args:
        speech: The words you want to say
    """
    text_to_speech(speech,"client_voice.mp3")
    with open("client_voice.mp3","rb") as f:
        bot.send_voice(context_variables['chat_id'],f)
    print(f"Speaking: {speech}")
    manager.add_message({"role":"assistant","content":f"[Audio Sent. Transcription:]{speech}[End]"})
    return {"result":"Audio sent!","transcription":speech}

bot.polling()