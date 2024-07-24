from telegram import Update
from telegram.ext import CallbackContext
from modules.models import UserPreferences
from modules.load import load_messages, load_categories, load_locations
from modules.database import get_session
from modules.utils import get_language, ALL_CATEGORIES, ALL_SUBCATEGORIES, WHOLE_FINLAND, ALL_CITIES

def save_language(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's language selection and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: main_menu;
            If the language is invalid: select_language.
    '''
    telegram_id = update.message.from_user.id
    session = get_session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()

    if user_preferences:
        language = user_preferences.language
    else:
        language = update.message.text
        if language in ['🇬🇧 English', '🇺🇦 Українська', '🇷🇺 Русский', '🇫🇮 Suomi']:
            user_preferences = UserPreferences(telegram_id=telegram_id, language=language)
            session.add(user_preferences)
            session.commit()
        else:
            update.message.reply_text('❗ Please select a valid language.')
            from conversation import select_language
            return select_language(update, context)
        
    from conversation import main_menu
    return main_menu(update, context)


def save_item_name(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's item input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_category;
            if not (3 <= len <= 64): add_new_item.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    if 'item' not in context.user_data:
        if not (3 <= len(update.message.text) <= 64):
            update.message.reply_text(messages['invalid_item'], parse_mode='HTML')
            from conversation import add_new_item
            return add_new_item(update, context)   
        context.user_data['item'] = update.message.text

    from conversation import select_category
    return select_category(update, context)


def save_category(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's category input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_subcategory;
            Invalid: select_category;
            If the choice is in ALL_CATEGORIES: save_product_category.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    if 'category' not in context.user_data:
        user_category = update.message.text
        if user_category not in categories_data:
            update.message.reply_text(messages['invalid_category'])
            from conversation import select_category
            return select_category(update, context)
        elif user_category.lower() in ALL_CATEGORIES:
            if language == '🇫🇮 Suomi':
                context.user_data['category'] = 'Kaikki kategoriat'
                context.user_data['subcategory'] = 'Kaikki alaluokat'
            elif language == '🇬🇧 English':
                context.user_data['category'] = 'All categories'
                context.user_data['subcategory'] = 'All subcategories'
            elif language == '🇺🇦 Українська':
                context.user_data['category'] = 'Всі категорії'
                context.user_data['subcategory'] = 'Всі підкатегорії'
            elif language == '🇷🇺 Русский':
                context.user_data['category'] = 'Все категории'
                context.user_data['subcategory'] = 'Все подкатегории'
            return save_product_category(update, context)
        else:
            context.user_data['category'] = update.message.text
    
    from conversation import select_subcategory
    return select_subcategory(update, context)


def save_subcategory(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's subcategory input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_product_category;
            Invalid: select_subcategory;
            If the choice is in ALL_SUBCATEGORIES: save_product_category.
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    if 'subcategory' not in context.user_data:
        user_subcategory = update.message.text
        if user_subcategory.lower() in ALL_SUBCATEGORIES:
            if language == '🇫🇮 Suomi':
                context.user_data['subcategory'] = 'Kaikki alaluokat'
            elif language == '🇬🇧 English':
                context.user_data['subcategory'] = 'All subcategories'
            elif language == '🇺🇦 Українська':
                context.user_data['subcategory'] = 'Всі підкатегорії'
            elif language == '🇷🇺 Русский':
                context.user_data['subcategory'] = 'Все подкатегории'
            return save_product_category(update, context)
        elif user_subcategory not in categories_data[context.user_data['category']]['subcategories']:
            update.message.reply_text(messages['invalid_subcategory'])
            from conversation import select_subcategory
            return select_subcategory(update, context)
        else:
            context.user_data['subcategory'] = update.message.text

    from conversation import select_product_category
    return select_product_category(update, context)


def save_product_category(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's product category input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_region;
            Invalid: select_product_category.
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)
    
    if 'product_category' not in context.user_data:
        user_product_category = update.message.text
        if user_product_category.lower() in ALL_CATEGORIES or user_product_category.lower() in ALL_SUBCATEGORIES:
            if language == '🇫🇮 Suomi':
                context.user_data['product_category'] = 'Kaikki tuoteluokat'
            elif language == '🇬🇧 English':
                context.user_data['product_category'] = 'All product categories'
            elif language == '🇺🇦 Українська':
                context.user_data['product_category'] = 'Всі категорії товарів'
            elif language == '🇷🇺 Русский':
                context.user_data['product_category'] = 'Все категории товаров'
        elif user_product_category.lower() not in ALL_CATEGORIES and user_product_category.lower() not in ALL_SUBCATEGORIES and user_product_category not in categories_data[context.user_data['category']]['subcategories'][context.user_data['subcategory']]['product_categories']:
            update.message.reply_text(messages['invalid_product_category'])
            from conversation import select_product_category
            return select_product_category(update, context)
        else:
            context.user_data['product_category'] = update.message.text
    
    from conversation import select_region
    return select_region(update, context)


def save_region(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's region input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_city;
            Invalid: select_region;
            If the choice is in WHOLE_FINLAND: save_area.
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    if 'region' not in context.user_data:
        user_region = update.message.text
        if user_region not in locations_data:
            update.message.reply_text(messages['invalid_region'])
            from conversation import select_region
            return select_region(update, context)
        if user_region.lower() in WHOLE_FINLAND:
            context.user_data['region'] = update.message.text
            if language == '🇫🇮 Suomi':
                context.user_data['city'] = 'Kaikki kaupungit'
                context.user_data['area'] = 'Kaikki alueet'
            elif language == '🇬🇧 English':
                context.user_data['city'] = 'All cities'
                context.user_data['area'] = 'All areas'
            elif language == '🇺🇦 Українська':
                context.user_data['city'] = 'Всі міста'
                context.user_data['area'] = 'Всі області'
            elif language == '🇷🇺 Русский':
                context.user_data['city'] = 'Все города'
                context.user_data['area'] = 'Все области'
            return save_area(update, context)
        else:
            context.user_data['region'] = update.message.text

    from conversation import select_city
    return select_city(update, context)


def save_city(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's city input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_area;
            Invalid: select_city;
            If the choice is in ALL_CITIES: save_area.
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    if 'city' not in context.user_data:
        user_city = update.message.text
        if user_city.lower() not in WHOLE_FINLAND and user_city not in locations_data[context.user_data['region']]['cities']:
            update.message.reply_text(messages['invalid_city'])
            from conversation import select_city
            return select_city(update, context)
        if user_city.lower() in ALL_CITIES:
            context.user_data['city'] = update.message.text
            if language == '🇫🇮 Suomi':
                context.user_data['area'] = 'Kaikki alueet'
            elif language == '🇬🇧 English':
                context.user_data['area'] = 'All areas'
            elif language == '🇺🇦 Українська':
                context.user_data['area'] = 'Всі області'
            elif language == '🇷🇺 Русский':
                context.user_data['area'] = 'Все области'
            return save_area(update, context)
        else:
            context.user_data['city'] = update.message.text
        
    from conversation import select_area
    return select_area(update, context)


def save_area(update: Update, context: CallbackContext) -> int:
    '''
    Handle the user's area input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (CallbackContext): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: save_data;
            Invalid: select_area;
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    if 'area' not in context.user_data:
        user_area = update.message.text
        if user_area.lower() in WHOLE_FINLAND or user_area.lower() in ALL_CITIES :
            if language == '🇫🇮 Suomi':
                context.user_data['product_category'] = 'Kaikki alueet'
            elif language == '🇬🇧 English':
                context.user_data['product_category'] = 'All areas'
            elif language == '🇺🇦 Українська':
                context.user_data['product_category'] = 'Всі райони'
            elif language == '🇷🇺 Русский':
                context.user_data['product_category'] = 'Все районы'
        if user_area.lower() not in WHOLE_FINLAND and user_area not in locations_data[context.user_data['region']]['cities'][context.user_data['city']]['areas']:
            update.message.reply_text(messages['invalid_area'])
            from conversation import select_area
            return select_area(update, context)
        else:
            context.user_data['area'] = update.message.text

    from conversation import save_data
    return save_data(update, context)
