from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.database import get_session
from modules.load import load_categories, load_locations, load_messages
from modules.models import UserPreferences, ToriItem
from modules.constants import *
from modules.utils import get_language

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Start the conversation and display a welcome message.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (select_language).
    '''
    await update.message.reply_text('👋 Hi! Welcome to ToriScan! \n\n🤖 ToriScan is an unofficial Telegram bot that notifies users when a new item appears on tori.fi.\n🧑‍💻 Developer: @arealibusadrealiora\n\n<i>ToriScan is not affiliated with tori.fi or Schibsted Media Group.</i>', parse_mode='HTML')
    return await select_language(update, context)

async def start_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Start the conversation and display a welcome message in case if user blocked the bot or anything.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (select_language).
    '''
    await update.message.reply_text('👋 Hi! Welcome back to ToriScan! \n\n🤖 ToriScan is an unofficial Telegram bot that notifies users when a new item appears on tori.fi.\n🧑‍💻 Developer: @arealibusadrealiora\n\n<i>ToriScan is not affiliated with tori.fi or Schibsted Media Group.</i>', parse_mode='HTML')
    return await select_language(update, context)

async def add_new_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Initiate the process of adding a new item to track.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: ITEM;
            If there's more than 10 items on the list: main_menu.
    '''
    context.user_data.pop('item', None)
    context.user_data.pop('category', None)
    context.user_data.pop('subcategory', None)
    context.user_data.pop('product_category', None)
    context.user_data.pop('locations', None)

    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)
    
    session = get_session()
    user_item_count = session.query(ToriItem).filter_by(telegram_id=telegram_id).count()
    session.close()

    if user_item_count >= 10:  # Limiting user to 10 items to avoid spam
        await update.message.reply_text(messages['more_10'])
        return await main_menu(update, context)

    await update.message.reply_text(messages['enter_item'], parse_mode='HTML')

    return ITEM

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the language selection menu or proceed to the main menu if language is already set.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (main_menu).
    '''
    telegram_id = update.message.from_user.id
    session = get_session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()

    if user_preferences:
        context.user_data['language'] = user_preferences.language
    else:
        await update.message.reply_text('💬 Please select your preferred language:', reply_markup=ReplyKeyboardMarkup([['🇬🇧 English', '🇺🇦 Українська', '🇷🇺 Русский', '🇫🇮 Suomi']], one_time_keyboard=True))
        return LANGUAGE

    return await main_menu(update, context)

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the category selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (CATEGORY).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    categories_data = load_categories(language)
    messages = load_messages(language)

    keyboard = [[category] for category in categories_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(messages['select_category'], reply_markup=reply_markup)

    return CATEGORY

async def select_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the subcategory selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
    await update.message.reply_text(messages['select_subcategory'], reply_markup=reply_markup)

    return SUBCATEGORY

async def select_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the product category selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: 
            Default: Next state for the conversation (PRODUCT_CATEGORY).
            If there are no product categories for that subcategory: select_region
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
        return await select_region(update, context)
    
    keyboard = [[product_category] for product_category in product_categories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(messages['select_product_category'], reply_markup=reply_markup)

    return PRODUCT_CATEGORY

async def select_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the region selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation (REGION).
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)
    
    keyboard = [[region] for region in locations_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(messages['select_region'], reply_markup=reply_markup)

    return REGION

async def select_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Display the city selection menu.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
    await update.message.reply_text(messages['select_city'], reply_markup=reply_markup)

    return CITY

async def select_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        return await add_more_locations(update, context)
    
    keyboard = [[area] for area in areas]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(messages['select_area'], reply_markup=reply_markup)

    return AREA

async def add_more_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Ask user if they want to add another location to their search after selecting the first one.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: 
            Default: Next state for the conversation (MORE_LOCATIONS), if user wants to add more locations.
            If they're done adding location: save_data
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    keyboard = [[messages['yes'], messages['no']]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(messages['add_more_locations'], reply_markup=reply_markup)

    return MORE_LOCATIONS

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    await update.message.reply_text(messages['menu'], reply_markup=ReplyKeyboardMarkup([[messages['add_item'], messages['items'], messages['settings']]], one_time_keyboard=False))

    return MAIN_MENU

async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        await update.message.reply_text(messages['lets_add'])
        return await add_new_item(update, context)
    elif choice == messages['items']:
        return await show_items(update, context)
    elif choice == messages['settings']:
        return await show_settings_menu(update, context)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    message = await update.message.reply_text(messages['settings_menu'], reply_markup=reply_markup)
    context.user_data['settings_menu_message_id'] = message.message_id

    return SETTINGS_MENU

async def settings_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        await update.message.reply_text(messages['change_language_prompt'])
        session = get_session()
        session.query(UserPreferences).filter_by(telegram_id=telegram_id).delete()
        session.commit()
        session.close()
        return await select_language(update, context)
    elif choice == messages['contact_developer']:
        await update.message.reply_text(messages['contact_developer_prompt'], parse_mode='HTML')
    elif choice == messages['back']:
        return await main_menu(update, context)
    else:
        await update.message.reply_text(messages['invalid_choice'])
        return await show_settings_menu(update, context)

async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        await update.message.reply_text(messages['items_list'])
        items_message = ''
        for item in user_items:
            item_info = messages['item'].format(item=item.item)
            item_info += messages['category'].format(category=item.category)
            if item.subcategory != 'null':
                item_info += messages['subcategory'].format(subcategory=item.subcategory)
            if item.product_category != 'null':
                item_info += messages['product_type'].format(product_category=item.product_category)
                
            item_info += messages['locations_header']
            for location in item.locations:
                item_info += "  📍 " + location['region']
                if location['city'].lower() not in ALL_CITIES:
                    item_info += f", {location['city']}"
                if 'area' in location and location['area'].lower() not in ALL_AREAS:
                    item_info += f", {location['area']}"
                item_info += "\n"
            
            item_info += messages['added_time'].format(time=item.added_time.strftime('%Y-%m-%d %H:%M:%S'))

            remove_button = InlineKeyboardButton(messages['remove_item'], callback_data=str(item.id))
            keyboard = [[remove_button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            items_message += item_info
            await update.message.reply_text(items_message, parse_mode='HTML', reply_markup=reply_markup)
            items_message = ''
    else:
        await update.message.reply_text(messages['no_items'])
    
    session.close()
    
    return MAIN_MENU

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    required_data = ['item', 'category', 'subcategory', 'product_category', 'locations']
    missing_data = [key for key in required_data if key not in context.user_data]

    if missing_data:
        await update.message.reply_text(messages['missing_data'].format(missing=', '.join(missing_data)))
        return ConversationHandler.END

    item = context.user_data['item']
    category = context.user_data['category']
    subcategory = context.user_data['subcategory']
    product_category = context.user_data['product_category']
    
    locations = context.user_data['locations']
    locations.sort(key=lambda x: (
        x['region'].lower() in WHOLE_FINLAND, 
        x['city'].lower() in ALL_CITIES,      
        x.get('area', '').lower() in ALL_AREAS
    ))
    
    final_locations = []
    region_coverages = {}
    
    for loc in locations:
        region = loc['region']
        if region.lower() in WHOLE_FINLAND:
            final_locations = [loc]
            break
        if region in region_coverages:
            if region_coverages[region] == 'ALL':
                continue
            if loc['city'].lower() in ALL_CITIES:
                region_coverages[region] = 'ALL'
                final_locations = [l for l in final_locations if l['region'] != region]
                final_locations.append(loc)
                continue
        else:
            if loc['city'].lower() in ALL_CITIES:
                region_coverages[region] = 'ALL'
            else:
                region_coverages[region] = 'PARTIAL'
            final_locations.append(loc)
    
    locations = final_locations
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

    has_whole_finland = any(loc['region'].lower() in WHOLE_FINLAND for loc in locations)
    
    if not has_whole_finland:
        for loc in locations:
            region = loc['region']
            city = loc['city']
            area = loc.get('area')
            
            if region.lower() not in WHOLE_FINLAND:
                if city.lower() not in ALL_CITIES:
                    if area and area.lower() not in ALL_AREAS:
                        area_code = locations_data[region]['cities'][city]['areas'][area]
                        tori_link += f'&location={area_code}'
                    else:
                        city_code = locations_data[region]['cities'][city]['city_code']
                        tori_link += f'&location={city_code}'
                else:
                    region_code = locations_data[region]['region_code']
                    tori_link += f'&location={region_code}'

    tori_link += '&sort=PUBLISHED_DESC'

    new_item = ToriItem(
        item=item,
        category=category,
        subcategory=subcategory,
        product_category=product_category,
        locations=locations,
        telegram_id=telegram_id,
        link=tori_link
    )
    
    session.add(new_item)
    session.commit()

    message = messages['item_added']
    message += messages['item'].format(item=item)
    message += messages['category'].format(category=category)
    if subcategory.lower() not in ALL_SUBCATEGORIES:
        message += messages['subcategory'].format(subcategory=subcategory)
    if product_category.lower() not in ALL_PRODUCT_CATEGORIES:
        message += messages['product_type'].format(product_category=product_category) 
    message += messages['locations_header']
    if has_whole_finland:
        for loc in locations:
            if loc['region'].lower() in WHOLE_FINLAND:
                message += f"  📍 {loc['region']}\n"
                break
    else:
        for loc in locations:
            message += "  📍 " + loc['region']
            if loc['city'].lower() not in ALL_CITIES:
                message += f", {loc['city']}"
            if 'area' in loc and loc['area'].lower() not in ALL_AREAS:
                message += f", {loc['area']}"
            message += "\n"  
    message += f"{messages['added_time'].format(time=new_item.added_time.strftime('%Y-%m-%d %H:%M:%S'))}"
    #message += f'The search link for the item: {tori_link}'
    
    await update.message.reply_text(message, parse_mode='HTML')
    
    session.close()
    
    return await main_menu(update, context)
