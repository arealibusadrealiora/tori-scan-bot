from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters
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
    more_locations_response,
    more_categories_response,
    save_additional_filters_choice,
    save_dealer_segment,
    save_shipping_types,
    save_price_from,
    save_price_to
)
from modules.conversation import start, start_again, save_data, main_menu_choice, settings_menu_choice, show_items, main_menu, show_settings_menu

def setup_handlers(application: Application):
    new_user_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start),
                      CommandHandler('start', start)],
        states={
            SETTINGS_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, settings_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_item_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_category)],
            SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_product_category)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_region)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_area)],
            MORE_LOCATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, more_locations_response)],
            MORE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, more_categories_response)],
            ADDITIONAL_FILTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_additional_filters_choice)],
            DEALER_SEGMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_dealer_segment)],
            SHIPPING_TYPES: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_shipping_types)],
            PRICE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_price_from)],
            PRICE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_price_to)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="new_user_conversation"
    )

    returning_user_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start_again),
                      CommandHandler('start', start_again)],
        states={
            SETTINGS_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, settings_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_item_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_category)],
            SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_product_category)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_region)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_area)],
            MORE_LOCATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, more_locations_response)],
            MORE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, more_categories_response)],
            ADDITIONAL_FILTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_additional_filters_choice)],
            DEALER_SEGMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_dealer_segment)],
            SHIPPING_TYPES: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_shipping_types)],
            PRICE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_price_from)],
            PRICE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_price_to)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_data)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="returning_user_conversation",
        allow_reentry=True
    )

    application.add_handler(new_user_handler)
    application.add_handler(returning_user_handler)

    fallback_handler = ConversationHandler(
        entry_points=[
            CommandHandler('menu', main_menu),
            CommandHandler('settings', show_settings_menu),
            CommandHandler('items', show_items)
        ],
        states={
            SETTINGS_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, settings_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_choice),
                CommandHandler('menu', main_menu),
                CommandHandler('settings', show_settings_menu),
                CommandHandler('items', show_items)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="fallback_conversation",
        allow_reentry=True
    )
    
    application.add_handler(fallback_handler)
    application.add_handler(CallbackQueryHandler(remove_item))