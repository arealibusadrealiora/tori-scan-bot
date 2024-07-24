from telegram import Update
from telegram.ext import ConversationHandler, CallbackContext
from modules.models import UserPreferences, ToriItem
from modules.database import get_session
from modules.load import load_messages


# Constants for categories and locations
ALL_CATEGORIES = ['kaikki kategoriat', 'all categories', 'все категории', 'всі категорії']
ALL_SUBCATEGORIES = ['kaikki alaluokat', 'all subcategories', 'все подкатегории', 'всі підкатегорії']
ALL_PRODUCT_CATEGORIES = ['kaikki tuoteluokat', 'all product categories', 'все категории товаров', 'всі категорії товарів']
WHOLE_FINLAND = ['koko suomi', 'whole finland', 'вся финляндия', 'вся фінляндія']
ALL_CITIES = ['kaikki kaupungit', 'all cities', 'все города', 'всі міста']
ALL_AREAS = ['kaikki alueet', 'all areas', 'все области', 'всі райони']


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
