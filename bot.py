"""
Tori.fi Telegram Bot - Main Entry Point
Monitors Tori.fi listings and sends notifications to users based on their preferences.
"""
import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from modules.jobs import setup_jobs
from modules.handlers import setup_handlers

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    '''
    The main function that sets up the bot and handles the conversation.
    '''
    # Retrieve the bot token from environment variables
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise ValueError("No BOT_TOKEN provided in .env file")

    application = ApplicationBuilder().token(token).build()

    setup_handlers(application)
    setup_jobs(application.job_queue)

    application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
