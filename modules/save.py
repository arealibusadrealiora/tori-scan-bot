from telegram import Update
from telegram.ext import ContextTypes
from modules.models import UserPreferences
from modules.load import load_messages, load_categories, load_locations
from modules.database import get_session
from modules.utils import get_language, ALL_CATEGORIES, ALL_SUBCATEGORIES, WHOLE_FINLAND, ALL_CITIES
from modules.conversation import (
    main_menu,
    select_language,
    add_new_item,
    select_category,
    select_subcategory,
    select_product_category,
    select_region,
    select_city,
    select_area,
    save_data
)

async def save_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's language selection and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
            await update.message.reply_text('❗ Please select a valid language.')
            return await select_language(update, context)
        
    return await main_menu(update, context)

async def save_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's item input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
            await update.message.reply_text(messages['invalid_item'], parse_mode='HTML')
            return await add_new_item(update, context)   
        context.user_data['item'] = update.message.text

    return await select_category(update, context)

async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's category input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
            await update.message.reply_text(messages['invalid_category'])
            return await select_category(update, context)
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
            return await save_product_category(update, context)
        else:
            context.user_data['category'] = update.message.text
    
    return await select_subcategory(update, context)

async def save_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's subcategory input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
            return await save_product_category(update, context)
        elif user_subcategory not in categories_data[context.user_data['category']]['subcategories']:
            await update.message.reply_text(messages['invalid_subcategory'])
            return await select_subcategory(update, context)
        else:
            context.user_data['subcategory'] = update.message.text

    return await select_product_category(update, context)

async def save_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's product category input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
            await update.message.reply_text(messages['invalid_product_category'])
            return await select_product_category(update, context)
        else:
            context.user_data['product_category'] = update.message.text
    
    return await select_region(update, context)

async def save_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's region input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
        if user_region.lower() in WHOLE_FINLAND:
            if language == '🇫🇮 Suomi':
                context.user_data['region'] = 'Koko Suomi'
                context.user_data['city'] = 'Kaikki kaupungit'
                context.user_data['area'] = 'Kaikki alueet'
            elif language == '🇬🇧 English':
                context.user_data['region'] = 'Whole Finland'
                context.user_data['city'] = 'All cities'
                context.user_data['area'] = 'All areas'
            elif language == '🇺🇦 Українська':
                context.user_data['region'] = 'Вся Фінляндія'
                context.user_data['city'] = 'Всі міста'
                context.user_data['area'] = 'Всі області'
            elif language == '🇷🇺 Русский':
                context.user_data['region'] = 'Вся Финляндия'
                context.user_data['city'] = 'Все города'
                context.user_data['area'] = 'Все области'
            return await save_area(update, context)
        elif user_region not in locations_data:
            await update.message.reply_text(messages['invalid_region'])
            return await select_region(update, context)
        else:
            context.user_data['region'] = update.message.text
    
    return await select_city(update, context)

async def save_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's city input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
        if user_city.lower() in ALL_CITIES:
            context.user_data['city'] = update.message.text
            if language == '🇫🇮 Suomi':
                context.user_data['area'] = 'Kaikki alueet'
                context.user_data['city'] = 'Kaikki kaupungit'
            elif language == '🇬🇧 English':
                context.user_data['area'] = 'All areas'
                context.user_data['city'] = 'All cities'
            elif language == '🇺🇦 Українська':
                context.user_data['area'] = 'Всі області'
                context.user_data['city'] = 'Всі міста'
            elif language == '🇷🇺 Русский':
                context.user_data['area'] = 'Все области'
                context.user_data['city'] = 'Все города'
            return await save_area(update, context)
        elif user_city.lower() not in WHOLE_FINLAND and user_city not in locations_data[context.user_data['region']]['cities']:
            await update.message.reply_text(messages['invalid_city'])
            return await select_city(update, context)
        else:
            context.user_data['city'] = update.message.text

    return await select_area(update, context)

async def save_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's area input and save it to the database.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: save_data;
            Invalid: select_area.
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
            await update.message.reply_text(messages['invalid_area'])
            return await select_area(update, context)
        else:
            context.user_data['area'] = update.message.text

    return await save_data(update, context)
