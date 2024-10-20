from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from modules.utils import remove_item, cancel
from modules.constants import *
from modules.save import (
    save_language,
    save_item_name,
    save_category,
    save_subcategory,
    save_product_category,
    save_region,
    save_city,
    save_area,
)
from modules.conversation import start, start_again, save_data, main_menu_choice, settings_menu_choice, show_items

async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if 'conversation_started' not in context.user_data:
        context.user_data['conversation_started'] = True
        return await start(update, context)
    else:
        return await start_again(update, context)

def setup_handlers(application: Application):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start_wrapper),
                      CommandHandler('start', start_wrapper)],
        states={
            SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_menu_choice)],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_item_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_category)],
            SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_product_category)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_region)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_area)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_data)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    application.add_handler(CommandHandler('items', show_items))
    application.add_handler(CallbackQueryHandler(remove_item))
    application.add_handler(conv_handler)