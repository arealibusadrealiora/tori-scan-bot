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
