import logging
import os
import asyncio
from telegram.ext import ApplicationBuilder, ContextTypes
from modules.jobs import setup_jobs
from modules.handlers import setup_handlers

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation handler states
(LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, 
 REGION, CITY, AREA, CONFIRMATION, MAIN_MENU, SETTINGS_MENU) = range(11)

async def main():
    '''
    The main function that sets up the bot and handles the conversation.
    '''
    # Retrieve the bot token from environment variables/text file/hard-code it:
    #with open('token.txt', encoding='utf-8') as file:
    #     token = file.read().strip()
    token = os.getenv('TOKEN')
    if not token:
        raise ValueError("No TOKEN provided in environment variables")

    application = ApplicationBuilder().token(token).build()

    setup_handlers(application)
    setup_jobs(application.job_queue)

    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
