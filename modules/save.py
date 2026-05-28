from telegram import Update
from telegram.ext import ContextTypes
from modules.models import UserPreferences
from modules.load import load_messages, load_categories, load_locations
from modules.database import get_session
from modules.utils import get_language, update_locations_list, update_categories_list, ALL_CATEGORIES, ALL_SUBCATEGORIES, WHOLE_FINLAND, ALL_CITIES
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
    add_more_locations,
    add_more_categories,
    select_additional_filters,
    select_dealer_segment,
    select_shipping_types,
    select_price_from,
    select_price_to,
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
    
    if 'categories' not in context.user_data:
        context.user_data['categories'] = []

    context.user_data['product_category'] = update.message.text

    new_category = {
        'category': context.user_data.pop('category'),
        'subcategory': context.user_data.pop('subcategory'),
        'product_category': context.user_data.pop('product_category')
    }
    context.user_data['categories'].append(new_category)
    
    if new_category['category'].lower() in ALL_CATEGORIES:
        return await select_region(update, context)
    
    return await add_more_categories(update, context)

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
            If the choice is in WHOLE_FINLAND: save_data.
    ''' 
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    locations_data = load_locations(language)
    messages = load_messages(language)

    user_region = update.message.text
    if user_region not in locations_data:
        await update.message.reply_text(messages['invalid_region'])
        return await select_region(update, context)

    if user_region.lower() in WHOLE_FINLAND:
        context.user_data['locations'] = []
        if language == '🇫🇮 Suomi':
            whole_finland_location = {
                'region': 'Koko Suomi',
                'city': 'Kaikki kaupungit',
                'area': 'Kaikki alueet'
            }
        elif language == '🇬🇧 English':
            whole_finland_location = {
                'region': 'Whole Finland',
                'city': 'All cities',
                'area': 'All areas'
            }
        elif language == '🇺🇦 Українська':
            whole_finland_location = {
                'region': 'Вся Фінляндія',
                'city': 'Всі міста',
                'area': 'Всі райони'
            }
        elif language == '🇷🇺 Русский':
            whole_finland_location = {
                'region': 'Вся Финляндия',
                'city': 'Все города',
                'area': 'Все области'
            }
        context.user_data['locations'] = [whole_finland_location]
        return await save_data(update, context)
    
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
                context.user_data['area'] = 'Всі райони'
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

    return await add_more_locations(update, context)

async def more_locations_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle user's response about adding more locations.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
             - select_region if user wants to add another location
             - save_data if user is done adding locations
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    if 'locations' not in context.user_data:
        context.user_data['locations'] = []

    if all(key in context.user_data for key in ['region', 'city', 'area']):
        current_location = {
            'region': context.user_data.pop('region'),
            'city': context.user_data.pop('city'),
            'area': context.user_data.pop('area')
        }
        
        context.user_data['locations'] = update_locations_list(
            context.user_data['locations'], 
            current_location
        )

    if update.message.text == messages['yes']:
        return await select_region(update, context)
    else:
        if not context.user_data['locations']:
            await update.message.reply_text("Error: No locations selected. Please try again.")
            return await select_region(update, context)
        return await select_additional_filters(update, context)

async def more_categories_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    if 'categories' not in context.user_data:
        context.user_data['categories'] = []

    if all(key in context.user_data for key in ['category', 'subcategory', 'product_category']):
        new_category = {
            'category': context.user_data.pop('category'),
            'subcategory': context.user_data.pop('subcategory'),
            'product_category': context.user_data.pop('product_category')
        }
        
        if not any(
            cat['category'] == new_category['category'] and
            cat['subcategory'] == new_category['subcategory'] and
            cat['product_category'] == new_category['product_category']
            for cat in context.user_data['categories']
        ):
            context.user_data['categories'].append(new_category)

    if update.message.text == messages['yes']:
        return await select_category(update, context)
    else:
        if not context.user_data['categories']:
            await update.message.reply_text("Error: No categories selected. Please try again.")
            return await select_category(update, context)
        return await select_region(update, context)

async def save_additional_filters_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle user's choice about adding additional filters.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
             - select_dealer_segment if user wants to add filters
             - save_data if user skips additional filters (with default values)
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    if update.message.text == messages['yes']:
        return await select_dealer_segment(update, context)
    else:
        # Set default values for all additional filters
        context.user_data['dealer_segments'] = ['yksityinen', 'yritys']  # All sellers
        context.user_data['shipping_types'] = ['all']  # All items
        context.user_data['price_from'] = None  # No minimum price
        context.user_data['price_to'] = None  # No maximum price
        return await save_data(update, context)

async def save_dealer_segment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's dealer segment input and save it to the context.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_shipping_types;
            Invalid: select_dealer_segment.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    user_choice = update.message.text

    valid_choices = [
        messages['dealer_segment_yksityinen'],
        messages['dealer_segment_yritys'],
        messages['dealer_segment_all']
    ]

    if user_choice not in valid_choices:
        await update.message.reply_text(messages['invalid_dealer_segment'])
        return await select_dealer_segment(update, context)

    if 'dealer_segments' not in context.user_data:
        context.user_data['dealer_segments'] = []

    if user_choice == messages['dealer_segment_yksityinen']:
        context.user_data['dealer_segments'] = ['yksityinen']
    elif user_choice == messages['dealer_segment_yritys']:
        context.user_data['dealer_segments'] = ['yritys']
    else:
        context.user_data['dealer_segments'] = ['yksityinen', 'yritys']

    return await select_shipping_types(update, context)

async def save_shipping_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's shipping types input and save it to the context.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_price_from;
            Invalid: select_shipping_types.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    user_choice = update.message.text

    valid_choices = [
        messages['shipping_types_toridiili'],
        messages['shipping_types_all']
    ]

    if user_choice not in valid_choices:
        await update.message.reply_text(messages['invalid_shipping_types'])
        return await select_shipping_types(update, context)

    if user_choice == messages['shipping_types_toridiili']:
        context.user_data['shipping_types'] = ['toridiili']
    else:
        context.user_data['shipping_types'] = ['all']

    return await select_price_from(update, context)

async def save_price_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's minimum price input and save it to the context.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: select_price_to;
            Invalid: select_price_from.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    user_input = update.message.text

    # Check if user wants to skip
    if user_input == messages['skip_price_from']:
        context.user_data['price_from'] = None
        return await select_price_to(update, context)

    # Parse the price
    try:
        price_from = int(user_input.strip())

        # Validate that price is positive
        if price_from > 0:
            context.user_data['price_from'] = price_from
            return await select_price_to(update, context)
    except ValueError:
        pass  # Will show error message below

    # Invalid format
    await update.message.reply_text(messages['invalid_price_from'])
    return await select_price_from(update, context)

async def save_price_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Handle the user's maximum price input and save it to the context.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: Next state for the conversation:
            Default: save_data;
            Invalid: select_price_to.
    '''
    telegram_id = update.message.from_user.id
    language = get_language(telegram_id)
    messages = load_messages(language)

    user_input = update.message.text

    # Check if user wants to skip
    if user_input == messages['skip_price_to']:
        context.user_data['price_to'] = None
        return await save_data(update, context)

    # Parse the price
    try:
        price_to = int(user_input.strip())

        # Validate that price is positive
        if price_to > 0:
            # Check if price_from exists and validate price_to >= price_from
            price_from = context.user_data.get('price_from')
            if price_from is not None and price_to < price_from:
                await update.message.reply_text(messages['invalid_price_to'])
                return await select_price_to(update, context)

            context.user_data['price_to'] = price_to
            return await save_data(update, context)
    except ValueError:
        pass  # Will show error message below

    # Invalid format
    await update.message.reply_text(messages['invalid_price_to'])
    return await select_price_to(update, context)
