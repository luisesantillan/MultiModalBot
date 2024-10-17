# MultiModalBot

[![Donate via Ko-Fi](https://img.shields.io/badge/Donate-Ko--fi-red?logo=ko-fi&style=for-the-badge)](https://ko-fi.com/rejekts)
[![Open In Colab](https://img.shields.io/badge/Colab-F9AB00?style=for-the-badge&logo=googlecolab&color=525252)](https://colab.research.google.com/github/luisesantillan/MultiModalBot/blob/main/MultiModalBot.ipynb)

MultiModalBot is an advanced AI-powered chatbot that can understand and process multiple types of input, including text, images, and audio. This versatile bot is designed to provide intelligent responses and assist users across various domains.

https://github.com/user-attachments/assets/be1ee618-79fa-4cb4-9efd-7289a2944232


## Features

- Multi-modal input processing (text, images, audio)
- Natural language understanding and generation
- Image recognition and analysis
- Speech-to-text and text-to-speech capabilities
- Customizable responses and knowledge base
- Easy integration with popular messaging platforms

## Installation

To install MultiModalBot, follow these steps:

```bash
git clone https://github.com/luisesantillan/MultiModalBot.git
cd MultiModalBot
pip install -r requirements.txt
```

## Usage

Setting up your own MultiModalBot is super easy and fun! Just follow these simple steps:

1. Create a new file called `.env` in the MultiModalBot folder.

2. Open the `.env` file and add your secret bot token and openai api key like this:

TELEGRAM_BOT_TOKEN=your_secret_token_here

OPENAI_API_KEY=your_secret_api_key_here

3. Save the `.env` file and close it.

4. Open your computer's terminal or command prompt.

5. Go to the MultiModalBot folder by typing:
```bash
cd MultiModalBot
```

6. Start your awesome bot by typing:
```bash
python start_telegram_bot.py
```

Your bot is now ready! Open Telegram and start chatting with it.

Cool things you can do with your bot:

- Send text messages, and it will reply accordingly!
- Send pictures, and it will tell you what it sees!
- Send voice messages, and it will understand what you say!
- Type /speak followed by some text, and it will speak that back to you!
- Type /model followed by a model name to change the openai model used for text generation.

Cool things the bot can do:

- Understand and respond to text messages
- Understand and respond to images
- Understand and respond to voice messages
- Speak back to you in text or voice
- Send images based on text prompts

## Credits

- OpenAI for providing such wonderful AI models!
- Telegram for providing a great platform for chatbots.
- pyTelegramBotAPI for making it easy to interact with Telegram bots.
- PollinationsAI for providing an easy tool for image generation.
