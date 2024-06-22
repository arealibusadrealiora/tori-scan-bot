from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from conversation import start, save_data, main_menu_choice, settings_menu_choice, show_items, remove_item, cancel
from load import save_language, save_item_name, save_category, save_subcategory, save_product_category, save_region, save_city, save_area

def setup_handlers(updater):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, start)],
        states={
            SETTINGS_MENU: [MessageHandler(Filters.text & ~Filters.command, settings_menu_choice)],
            LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, save_language)],
            ITEM: [MessageHandler(Filters.text & ~Filters.command, save_item_name)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_category)],
            SUBCATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, save_product_category)],
            REGION: [MessageHandler(Filters.text & ~Filters.command, save_region)],
            CITY: [MessageHandler(Filters.text & ~Filters.command, save_city)],
            AREA: [MessageHandler(Filters.text & ~Filters.command, save_area)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, save_data)],
            MAIN_MENU: [MessageHandler(Filters.text & ~Filters.command, main_menu_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('items', show_items))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_item))
    updater.dispatcher.add_handler(conv_handler)
