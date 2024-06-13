from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot import LANGUAGE, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, get_language, main_menu, get_session, save_data
from loaders import load_categories, load_locations, load_messages
from models import UserPreferences

def select_language(update: Update, context: CallbackContext) -> int:
    '''
    Display the language selection menu or proceed to the main menu if language is already set.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (main_menu).
    '''
    telegram_id = update.message.from_user.id
    session = get_session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()

    if user_preferences:
        context.user_data['language'] = user_preferences.language
    else:
        update.message.reply_text('💬 Please select your preferrable language:', reply_markup=ReplyKeyboardMarkup([['🇬🇧 English', '🇺🇦 Українська', '🇷🇺 Русский', '🇫🇮 Suomi']], one_time_keyboard=True))
        return LANGUAGE

    return main_menu(update, context)

def select_category(update: Update, context: CallbackContext) -> int:
    '''
    Display the category selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (CATEGORY).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    keyboard = [[category] for category in categories_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_category'], reply_markup=reply_markup)

    return CATEGORY


def select_subcategory(update: Update, context: CallbackContext) -> int:
    '''
    Display the subcategory selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (SUBCATEGORY).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    subcategories = categories_data[context.user_data['category']]['subcategories']
    keyboard = [[subcategory] for subcategory in subcategories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_subcategory'], reply_markup=reply_markup)

    return SUBCATEGORY


def select_product_category(update: Update, context: CallbackContext) -> int:
    '''
    Display the product category selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: 
            Default: Next state for the conversation (PRODUCT_CATEGORY).
            If there is no product categories for that subcategory: select_region
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    product_categories = categories_data[context.user_data['category']]['subcategories'][context.user_data['subcategory']].get('product_categories')
    if not product_categories:
        if language == '🇫🇮 Suomi':
            context.user_data['product_category'] = 'Kaikki tuoteluokat'
        elif language == '🇬🇧 English':
            context.user_data['product_category'] = 'All product categories'
        elif language == '🇺🇦 Українська':
            context.user_data['product_category'] = 'Всі категорії товарів'
        elif language == '🇷🇺 Русский':
            context.user_data['product_category'] = 'Все категории товаров'
        return select_region(update, context)
    
    keyboard = [[product_category] for product_category in product_categories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_product_category'], reply_markup=reply_markup)

    return PRODUCT_CATEGORY


def select_region(update: Update, context: CallbackContext) -> int:
    '''
    Display the region selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (REGION).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)
    
    keyboard = [[region] for region in locations_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_region'], reply_markup=reply_markup)

    return REGION


def select_city(update: Update, context: CallbackContext) -> int:
    '''
    Display the city selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (CITY).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    cities = locations_data[context.user_data['region']]['cities']
    keyboard = [[city] for city in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_city'], reply_markup=reply_markup)

    return CITY


def select_area(update: Update, context: CallbackContext) -> int:
    '''
    Display the area selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (AREA).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    areas = locations_data[context.user_data['region']]['cities'][context.user_data['city']].get('areas', {})
    if not areas:
        return save_data(update, context)
    keyboard = [[area] for area in areas]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages['select_area'], reply_markup=reply_markup)

    return AREA