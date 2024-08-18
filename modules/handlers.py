from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters
from modules.utils import remove_item, cancel
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

# Conversation handler states
LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, CONFIRMATION, MAIN_MENU, SETTINGS_MENU = range(11)

def setup_handlers(application: Application):
    from modules.conversation import start, save_data, main_menu_choice, settings_menu_choice, show_items

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
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
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('items', show_items))
    application.add_handler(CallbackQueryHandler(remove_item))
    application.add_handler(conv_handler)
