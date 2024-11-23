from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes
from modules.models import UserPreferences, ToriItem
from modules.database import get_session
from modules.load import load_messages
from modules.constants import *

async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Remove the selected item from the user's list.
    Args:
        update (Update): The update object containing the user's callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
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
        await query.message.reply_text(messages['item_removed'].format(itemname=item.item))
    else:
        await query.message.reply_text(messages['item_not_found'])
    session.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Cancel the conversation.
    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object for maintaining conversation state.
    Returns:
        int: The end state of the conversation.
    '''
    await update.message.reply_text('Conversation cancelled.')
    return ConversationHandler.END

def get_language(telegram_id: int) -> str:
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

def is_location_covered(new_location: dict, existing_location: dict) -> bool:
    '''
    Check if a location is already covered by an existing location based on hierarchy.
    Args:
        new_location (dict): The new location to check
        existing_location (dict): An existing location to check against 
    Returns:
        bool: True if the new location is already covered by the existing location
    '''
    if existing_location['region'].lower() in WHOLE_FINLAND:
        return True
    if new_location['region'] != existing_location['region']:
        return False
    if new_location['city'].lower() in ALL_CITIES:
        return False
    if existing_location['city'].lower() in ALL_CITIES:
        return True  
    if new_location['city'] != existing_location['city']:
        return False
    if new_location.get('area', '').lower() in ALL_AREAS:
        return False 
    if existing_location.get('area', '').lower() in ALL_AREAS:
        return True 

    return new_location.get('area') == existing_location.get('area')

def update_locations_list(locations: list, new_location: dict) -> list:
    '''
    Update the locations list based on hierarchy rules.
    Args:
        locations (list): Current list of locations
        new_location (dict): New location to be added
    Returns:
        list: Updated list of locations
    '''
    if new_location['region'].lower() in WHOLE_FINLAND:
        return [new_location]

    if new_location['city'].lower() in ALL_CITIES:
        return [loc for loc in locations if loc['region'] != new_location['region']] + [new_location]

    if new_location.get('area', '').lower() in ALL_AREAS:
        return [loc for loc in locations if not (
            loc['region'] == new_location['region'] and 
            loc['city'] == new_location['city']
        )] + [new_location]

    for existing_location in locations:
        if is_location_covered(new_location, existing_location):
            return locations 

    return locations + [new_location]

def update_categories_list(categories: list, new_category: dict) -> list:
    '''
    Update the categories list based on hierarchy rules.
    Args:
        categories (list): Current list of categories
        new_category (dict): New category to be added containing category, subcategory, and product_category
    Returns:
        list: Updated list of categories
    '''
    if new_category['category'].lower() in ALL_CATEGORIES:
        return [new_category]

    if new_category['subcategory'].lower() in ALL_SUBCATEGORIES:
        return [cat for cat in categories if cat['category'] != new_category['category']] + [new_category]

    if new_category['product_category'].lower() in ALL_PRODUCT_CATEGORIES:
        return [cat for cat in categories if not (
            cat['category'] == new_category['category'] and 
            cat['subcategory'] == new_category['subcategory']
        )] + [new_category]

    for existing_cat in categories:
        if (existing_cat['category'].lower() in ALL_CATEGORIES or
            (existing_cat['category'] == new_category['category'] and 
             existing_cat['subcategory'].lower() in ALL_SUBCATEGORIES) or
            (existing_cat['category'] == new_category['category'] and
             existing_cat['subcategory'] == new_category['subcategory'] and
             existing_cat['product_category'].lower() in ALL_PRODUCT_CATEGORIES)):
            return categories

    for existing_cat in categories:
        if (existing_cat['category'] == new_category['category'] and
            existing_cat['subcategory'] == new_category['subcategory'] and
            existing_cat['product_category'] == new_category['product_category']):
            return categories

    return categories + [new_category]
