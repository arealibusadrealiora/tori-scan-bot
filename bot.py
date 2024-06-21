import logging
import requests
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from conversation import select_language, add_new_item
from datetime import datetime
from models import UserPreferences, ToriItem
from database import get_session
from load import load_categories, load_locations, load_messages
from save import save_item_name, save_language, save_category, save_subcategory, save_product_category, save_region, save_city, save_area
from jobs import setup_jobs

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation handler states
LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, CONFIRMATION, MAIN_MENU, SETTINGS_MENU = range(11)

# Constants for categories and locations
ALL_CATEGORIES = ['kaikki kategoriat', 'all categories', 'все категории', 'всі категорії']
ALL_SUBCATEGORIES = ['kaikki alaluokat', 'all subcategories', 'все подкатегории', 'всі підкатегорії']
ALL_PRODUCT_CATEGORIES = ['kaikki tuoteluokat', 'all product categories', 'все категории товаров', 'всі категорії товарів']
WHOLE_FINLAND = ['koko suomi', 'whole finland', 'вся финляндия', 'вся фінляндія']
ALL_CITIES = ['kaikki kaupungit', 'all cities', 'все города', 'всі міста']
ALL_AREAS = ['kaikki alueet', 'all areas', 'все области', 'всі райони']


def save_data(update: Update, context: CallbackContext) -> int:
    '''
    Save the user data and generate the search link.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation (main_menu).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    locations_data = load_locations(language)
    messages = load_messages(language)

    session = get_session()

    required_data = ['item', 'category', 'subcategory', 'product_category', 'region', 'city', 'area']
    missing_data = [key for key in required_data if key not in context.user_data]

    if missing_data:
        update.message.reply_text(messages['missing_data'].format(missing=', '.join(missing_data)))
        return ConversationHandler.END
    else:
        item = context.user_data['item']
        category = context.user_data['category']
        subcategory = context.user_data['subcategory']
        product_category = context.user_data['product_category']
        region = context.user_data['region']
        city = context.user_data['city']
        area = context.user_data['area']
        telegram_id = update.message.from_user.id
        
        tori_link = f'https://beta.tori.fi/recommerce-search-page/api/search/SEARCH_ID_BAP_COMMON?q={item.lower()}'
        if category.lower() not in ALL_CATEGORIES:
            if subcategory.lower() not in ALL_SUBCATEGORIES:
                if product_category.lower() not in ALL_PRODUCT_CATEGORIES:
                    product_category_code = categories_data[category]['subcategories'][subcategory]['product_categories'][product_category]
                    tori_link += f'&product_category={product_category_code}'
                else:
                    subcategory_code = categories_data[category]['subcategories'][subcategory]['subcategory_code']
                    tori_link += f'&sub_category={subcategory_code}'
            else:
                category_code = categories_data[category]['category_code']
                tori_link += f'&category={category_code}'
        if region.lower() not in WHOLE_FINLAND:
            if city.lower() not in ALL_CITIES:
                if area.lower() not in ALL_AREAS:
                    area_code = locations_data[region]['cities'][city]['areas'][area]
                    tori_link += f'&location={area_code}'
                else:
                    city_code = locations_data[region]['cities'][city]['city_code']
                    tori_link += f'&location={city_code}'
            else:
                region_code = locations_data[region]['region_code']
                tori_link += f'&location={region_code}'
        tori_link += '&sort=PUBLISHED_DESC'

        new_item = ToriItem(item=item, category=category, subcategory=subcategory, product_category=product_category, region=region, city=city, area=area, telegram_id=telegram_id, link=tori_link)
        
        session.add(new_item)
        session.commit()

        message = messages['item_added']
        message += messages['item'].format(item=item)
        message += messages['category'].format(category=category)
        if subcategory.lower() not in ALL_SUBCATEGORIES:
            message += messages['subcategory'].format(subcategory=subcategory)
        if product_category.lower() not in ALL_PRODUCT_CATEGORIES:
            message += messages['product_type'].format(product_category=product_category)
        message += messages['region'].format(region=region)
        if city.lower() not in ALL_CITIES:
            message += messages['city'].format(city=city)
        if area.lower() not in ALL_AREAS:
            message += messages['area'].format(area=area)
        message += messages['added_time'].format(time=new_item.added_time.strftime('%Y-%m-%d %H:%M:%S'))
        #message += f'Debug: The search link for the item: {tori_link}'

        update.message.reply_text(message, parse_mode='HTML')
        
        session.close()
        
        return main_menu(update, context)


def main_menu(update: Update, context: CallbackContext) -> int:
    '''
    Display the main menu with options to add an item, view items, or access settings.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation (MAIN_MENU).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    update.message.reply_text(messages['menu'], reply_markup=ReplyKeyboardMarkup([[messages['add_item'], messages['items'], messages['settings']]], one_time_keyboard=False))
    return MAIN_MENU


def main_menu_choice(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's choice from the main menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation based on user choice:
            'add_item': add_new_item;
            'items': show_items;
            'settings': show_settings_menu.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    choice = update.message.text
    if choice == messages['add_item']:
        update.message.reply_text(messages['lets_add'])
        return add_new_item(update, context) 
    elif choice == messages['items']:
        return show_items(update, context)
    elif choice == messages['settings']:
        return show_settings_menu(update, context) 
    

def show_settings_menu(update: Update, context: CallbackContext) -> int:
    '''
    Display the settings menu with options to change language or contact developer.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation (SETTINGS_MENU).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    keyboard = [
        [messages['change_language']],
        [messages['contact_developer']],
        [messages['back']]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    message = update.message.reply_text(messages['settings_menu'], reply_markup=reply_markup)
    context.user_data['settings_menu_message_id'] = message.message_id

    return SETTINGS_MENU


def settings_menu_choice(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's choice from the settings menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation based on user choice:
            'change_language': select_language;
            'contact_developer': messages a prompt 'contact_developer_prompt';
            'back': main_menu;
            'invalid_choice': show_settings_menu.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    choice = update.message.text

    if choice == messages['change_language']:
        update.message.reply_text(messages['change_language_prompt'])
        session = get_session()
        session.query(UserPreferences).filter_by(telegram_id=telegram_id).delete()
        session.commit()
        session.close()
        return select_language(update, context)
    elif choice == messages['contact_developer']:
        update.message.reply_text(messages['contact_developer_prompt'], parse_mode='HTML')
    elif choice == messages['back']:
        return main_menu(update, context)
    else:
        update.message.reply_text(messages['invalid_choice'])
        return show_settings_menu(update, context)


def show_items(update: Update, context: CallbackContext) -> int:
    '''
    Display the list of items added by the user with options to remove them.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The next state in the conversation (MAIN_MENU).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    session = get_session()
    
    user_items = session.query(ToriItem).filter_by(telegram_id=telegram_id).all()
    
    if user_items:
        update.message.reply_text(messages['items_list'])
        items_message = ''
        for item in user_items:
            item_info = messages['item'].format(item=item.item)
            item_info += messages['category'].format(category=item.category)
            if item.subcategory != 'null':
                item_info += messages['subcategory'].format(subcategory=item.subcategory)
            if item.product_category != 'null':
                item_info += messages['product_type'].format(product_category=item.product_category)
            item_info += messages['region'].format(region=item.region)
            if item.city != 'null':
                item_info += messages['city'].format(city=item.city)
            if item.area != 'null':
                item_info += messages['area'].format(area=item.area)
            item_info += messages['added_time'].format(time=item.added_time.strftime('%Y-%m-%d %H:%M:%S'))

            remove_button = InlineKeyboardButton(messages['remove_item'], callback_data=str(item.id))
            keyboard = [[remove_button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            items_message += item_info
            update.message.reply_text(items_message, parse_mode='HTML', reply_markup=reply_markup)
            items_message = ''
    else:
        update.message.reply_text(messages['no_items'])
    session.close()
    
    return MAIN_MENU


def remove_item(update: Update, context: CallbackContext) -> None:
    '''
    Remove the selected item from the user's list.
    Args:
        update (Update): The update object containing the user's callback query.
        context (CallbackContext): The context object for maintaining conversation state.
    '''
    query = update.callback_query
    telegram_id = query.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    session = get_session()
    
    item_id = int(query.data)
    item = session.query(ToriItem).filter_by(id=item_id).first()

    if item:
        session.query(ToriItem).filter_by(id=item_id).delete()
        session.commit()
        query.message.reply_text(messages['item_removed'].format(itemname=item.item))
    else:
        query.message.reply_text(messages['item_not_found'])
    session.close()


def cancel(update: Update, context: CallbackContext) -> int:
    '''
    Cancel the conversation.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: The end state of the conversation.
    '''
    update.message.reply_text('Conversation cancelled.')
    return ConversationHandler.END


def get_language(telegram_id):
    '''
    Get the user's preferred language.
    Args:
        telegram_id (int): The user's Telegram ID.
    Returns:
        str: The user's preferred language or the default language ('🇬🇧 English').
    '''
    session = get_session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user_preferences.language if user_preferences else '🇬🇧 English'


def main():
    '''
    The main function that sets up the bot and handles the conversation.
    '''
    with open('token.txt', encoding='utf-8') as file:
        token = file.read().strip()
    updater = Updater(token, use_context=True)
    job_queue = updater.job_queue

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, start)],
        states={
            SETTINGS_MENU: [MessageHandler(Filters.text & ~Filters.command, settings_menu_choice)],
            LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, save_language)],
            ITEM: [MessageHandler(Filters.text & ~Filters.command, save_item_name)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_category)],
            SUBCATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_product_category)],
            REGION: [MessageHandler(Filters.text & ~Filters.command, save_region)],
            CITY: [MessageHandler(Filters.text & ~Filters.command, save_city)],
            AREA: [MessageHandler(Filters.text & ~Filters.command, save_area)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, save_data)],
            MAIN_MENU: [MessageHandler(Filters.text & ~Filters.command, main_menu_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('items', show_items))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_item)) 
    updater.dispatcher.add_handler(conv_handler)

    setup_jobs(updater.job_queue)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()