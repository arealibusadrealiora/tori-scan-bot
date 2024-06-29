import logging
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from conversation import start, select_language, add_new_item
from datetime import datetime
from models import UserPreferences, ToriItem
from database import get_session
from load import load_categories, load_locations, load_messages
from save import save_item_name, save_language, save_category, save_subcategory, save_product_category, save_region, save_city, save_area
from jobs import setup_jobs
from handlers import setup_handlers


# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Conversation handler states
LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, CONFIRMATION, MAIN_MENU, SETTINGS_MENU = range(11)


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