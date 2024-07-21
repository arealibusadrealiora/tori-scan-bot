import logging
from telegram.ext import Updater
from modules.jobs import setup_jobs
from modules.handlers import setup_handlers


# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Conversation handler states
(LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, 
 REGION, CITY, AREA, CONFIRMATION, MAIN_MENU, SETTINGS_MENU) = range(11)


def main():
    '''
    The main function that sets up the bot and handles the conversation.
    '''
    with open('token.txt', encoding='utf-8') as file:
        token = file.read().strip()
    updater = Updater(token, use_context=True)
    job_queue = updater.job_queue

    setup_handlers(updater)
    setup_jobs(updater.job_queue)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()