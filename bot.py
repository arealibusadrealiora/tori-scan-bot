from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import DateTime
from datetime import datetime
import json
import requests

engine = create_engine('sqlite:///tori_data.db')
Base = declarative_base()

class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    language = Column(String)

class ToriItem(Base):
    __tablename__ = 'tori_items'

    id = Column(Integer, primary_key=True)
    item = Column(String)
    category = Column(Integer)
    subcategory = Column(Integer)
    product_category = Column(Integer)
    region = Column(Integer)
    city = Column(Integer)
    area = Column(Integer)
    telegram_id = Column(Integer)
    added_time = Column(DateTime, default=datetime.now)
    link = Column(String)
    latest_time = Column(DateTime) 

Base.metadata.create_all(engine)

LANGUAGE_SELECTION, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, CONFIRMATION, ADD_OR_SHOW_ITEMS, SETTINGS_MENU = range(10)

ALL_CATEGORIES = ["kaikki kategoriat", "all categories", "все категории", "всі категорії"]
ALL_SUBCATEGORIES = ["kaikki alaluokat", "all subcategories", "все подкатегории", "всі підкатегорії"]
ALL_PRODUCT_CATEGORIES = ["kaikki tuoteluokat", "all product categories", "все категории товаров", "всі категорії товарів"]
WHOLE_FINLAND = ["koko suomi", "whole finland", "вся финляндия", "вся фінляндія"]
ALL_CITIES = ["kaikki kaupungit", "all cities", "все города", "всі міста"]
ALL_AREAS = ["kaikki alueet", "all areas", "все области", "всі області"]

def load_categories(language: str) -> dict:
    with open(f'jsons/categories/{language}.json', encoding="utf-8") as f:
        categories_data = json.load(f)
    return categories_data

def load_locations(language: str) -> dict:
    with open(f'jsons/locations/{language}.json', encoding="utf-8") as f:
        locations_data = json.load(f)
    return locations_data

def load_messages(language: str) -> dict:
    with open(f'jsons/messages/{language}.json', encoding="utf-8") as f:
        messages_data = json.load(f)
    return messages_data

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Hi! Welcome to ToriScan!\n\nToriScan is an unofficial Telegram bot that notifies users when the new item is showing up on tori.fi.\nToriScan is not legally related to tori.fi or Schibsted Media Group.\n\nDeveloper: @arealibusadrealiora")
    
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        context.user_data['language'] = user_preferences.language
    else:
        update.message.reply_text("Please select your preferrable language:", reply_markup=ReplyKeyboardMarkup([['🇬🇧 English', '🇺🇦 Українська', '🇷🇺 Русский', '🇫🇮 Suomi']], one_time_keyboard=True))
        return LANGUAGE_SELECTION

    return add_or_show_items(update, context)

def language_selection(update: Update, context: CallbackContext) -> int:
    context.user_data.pop('item', None)
    context.user_data.pop('category', None)
    context.user_data.pop('subcategory', None)
    context.user_data.pop('product_category', None)
    context.user_data.pop('region', None)
    context.user_data.pop('city', None)
    context.user_data.pop('area', None)

    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
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
            update.message.reply_text("Please select a valid language.")
            return start(update, context)
    
    
    user_item_count = session.query(ToriItem).filter_by(telegram_id=telegram_id).count()
    session.close()

    messages = load_messages(language)
    
    if user_item_count >= 10:
        update.message.reply_text(messages["more_10"])
        return add_or_show_items(update, context)

    update.message.reply_text(messages["enter_item"], parse_mode="HTML")
    return CATEGORY

def select_category(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    categories_data = load_categories(language)
    messages = load_messages(language)

    if 'item' not in context.user_data:
        if not (3 <= len(update.message.text) <= 64):
            update.message.reply_text(messages["invalid_item"], parse_mode="HTML")
            return language_selection(update, context)   
        context.user_data['item'] = update.message.text

    keyboard = [[category] for category in categories_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_category"], reply_markup=reply_markup)
    return SUBCATEGORY

def select_subcategory(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    categories_data = load_categories(language)
    messages = load_messages(language)

    if 'category' not in context.user_data:
        user_category = update.message.text
        if user_category not in categories_data:
            update.message.reply_text(messages["invalid_category"])
            return select_category(update, context)
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
            return select_region(update, context)
        else:
            context.user_data['category'] = update.message.text

    subcategories = categories_data[context.user_data['category']]["subcategories"]
    keyboard = [[subcategory] for subcategory in subcategories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_subcategory"], reply_markup=reply_markup)
    return PRODUCT_CATEGORY

def select_product_category(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
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
            return select_region(update, context)
        elif user_subcategory not in categories_data[context.user_data['category']]["subcategories"]:
            update.message.reply_text(messages["invalid_subcategory"])
            return select_subcategory(update, context)
        else:
            context.user_data['subcategory'] = update.message.text

    product_categories = categories_data[context.user_data['category']]["subcategories"][context.user_data['subcategory']].get('product_categories')
    if not product_categories:
        if language == '🇫🇮 Suomi':
            context.user_data['product_category'] = 'Kaikki tuoteluokat'
        elif language == '🇬🇧 English':
            context.user_data['product_category'] = 'All product categories'
        elif language == '🇺🇦 Українська':
            context.user_data['product_category'] = 'Всі категорії товарів'
        elif language == '🇷🇺 Русский':
            context.user_data['product_category'] = 'Все категории товаров'
        return select_region(update, context)
    
    keyboard = [[product_category] for product_category in product_categories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_product_category"], reply_markup=reply_markup)
    return REGION

def select_region(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    categories_data = load_categories(language)
    locations_data = load_locations(language)
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
                context.user_data['product_category'] = 'Все категорії товаров'
        elif user_product_category.lower() not in ALL_CATEGORIES and user_product_category.lower() not in ALL_SUBCATEGORIES and user_product_category not in categories_data[context.user_data['category']]["subcategories"][context.user_data['subcategory']]["product_categories"]:
            update.message.reply_text(messages["invalid_product_category"])
            return select_product_category(update, context)
        else:
            context.user_data['product_category'] = update.message.text
    
    keyboard = [[region] for region in locations_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_region"], reply_markup=reply_markup)
    return CITY

def select_city(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    locations_data = load_locations(language)
    messages = load_messages(language)

    if 'region' not in context.user_data:
        user_region = update.message.text
        if user_region not in locations_data:
            update.message.reply_text(messages["invalid_region"])
            return select_region(update, context)
        if user_region.lower() in WHOLE_FINLAND:
            context.user_data['region'] = update.message.text
            if language == '🇫🇮 Suomi':
                context.user_data['city'] = 'Kaikki kaupungit'
                context.user_data['area'] = 'Kaikki alueet'
            elif language == '🇬🇧 English':
                context.user_data['city'] = 'All cities'
                context.user_data['area'] = 'All areas'
            elif language == '🇺🇦 Українська':
                context.user_data['city'] = 'Всі міста'
                context.user_data['area'] = 'Всі області'
            elif language == '🇷🇺 Русский':
                context.user_data['city'] = 'Все города'
                context.user_data['area'] = 'Все области'
            return save_data(update, context)
        else:
            context.user_data['region'] = update.message.text

    cities = locations_data[context.user_data['region']]["cities"]
    keyboard = [[city] for city in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_city"], reply_markup=reply_markup)
    return AREA

def select_area(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    locations_data = load_locations(language)
    messages = load_messages(language)
    
    if 'city' not in context.user_data:
        user_city = update.message.text
        if user_city.lower() not in WHOLE_FINLAND and user_city not in locations_data[context.user_data['region']]["cities"]:
            update.message.reply_text(messages["invalid_city"])
            return select_city(update, context)
        else:
            context.user_data['city'] = update.message.text

    areas = locations_data[context.user_data['region']]["cities"][context.user_data['city']].get('areas', {})
    if not areas:
        return save_data(update, context)
    keyboard = [[area] for area in areas]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(messages["select_area"], reply_markup=reply_markup)
    return CONFIRMATION

def save_data(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    categories_data = load_categories(language)
    locations_data = load_locations(language)
    messages = load_messages(language)
    
    if 'area' not in context.user_data:
        user_area = update.message.text
        if user_area.lower() not in WHOLE_FINLAND and user_area not in locations_data[context.user_data['region']]["cities"][context.user_data['city']]["areas"]:
            update.message.reply_text(messages["invalid_area"])
            return select_area(update, context)
        else:
            context.user_data['area'] = update.message.text

    required_data = ['item', 'category', 'subcategory', 'product_category', 'region', 'city', 'area']
    missing_data = [key for key in required_data if key not in context.user_data]

    if missing_data:
        update.message.reply_text(messages["missing_data"].format(missing=', '.join(missing_data)))
        return ConversationHandler.END
    else:
        item = context.user_data['item']
        category = context.user_data['category']
        subcategory = context.user_data['subcategory']
        product_category = context.user_data['product_category']
        region = context.user_data['region']
        city = context.user_data['city']
        area = context.user_data['area']
        telegram_id = update.message.from_user.id
        
        tori_link = f"https://beta.tori.fi/recommerce-search-page/api/search/SEARCH_ID_BAP_COMMON?q={item.lower()}"
        if category.lower() not in ALL_CATEGORIES:
            if subcategory.lower() not in ALL_SUBCATEGORIES:
                if product_category.lower() not in ALL_PRODUCT_CATEGORIES:
                    product_category_code = categories_data[category]["subcategories"][subcategory]["product_categories"][product_category]
                    tori_link += f"&product_category={product_category_code}"
                else:
                    subcategory_code = categories_data[category]["subcategories"][subcategory]["subcategory_code"]
                    tori_link += f"&sub_category={subcategory_code}"
            else:
                category_code = categories_data[category]["category_code"]
                tori_link += f"&category={category_code}"
        if region.lower() not in WHOLE_FINLAND:
            if city.lower() not in ALL_CITIES:
                if area.lower() not in ALL_AREAS:
                    area_code = locations_data[region]["cities"][city]["areas"][area]
                    tori_link += f"&location={area_code}"
                else:
                    city_code = locations_data[region]["cities"][city]["city_code"]
                    tori_link += f"&location={city_code}"
            else:
                region_code = locations_data[region]["region_code"]
                tori_link += f"&location={region_code}"
        tori_link += '&sort=PUBLISHED_DESC'

        new_item = ToriItem(item=item, category=category, subcategory=subcategory, product_category=product_category, region=region, city=city, area=area, telegram_id=telegram_id, link=tori_link)
        
        session.add(new_item)
        session.commit()

        message = messages["item_added"]
        message += messages["item"].format(item=item)
        message += messages["category"].format(category=category)
        if subcategory.lower() not in ALL_SUBCATEGORIES:
            message += messages["subcategory"].format(subcategory=subcategory)
        if product_category.lower() not in ALL_PRODUCT_CATEGORIES:
            message += messages["product_type"].format(product_category=product_category)
        message += messages["region"].format(region=region)
        if city.lower() not in ALL_CITIES:
            message += messages["city"].format(city=city)
        if area.lower() not in ALL_AREAS:
            message += messages["area"].format(area=area)
        message += messages["added_time"].format(time=new_item.added_time.strftime('%Y-%m-%d %H:%M:%S'))

        update.message.reply_text(message + f"Debug: The search link for the item: {tori_link}", parse_mode="HTML")
        
        session.close()
        
        return add_or_show_items(update, context)

def add_or_show_items(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    messages = load_messages(language)

    update.message.reply_text(messages["menu"], reply_markup=ReplyKeyboardMarkup([[messages["add_item"], messages["items"], messages["settings"]]], one_time_keyboard=False))
    return ADD_OR_SHOW_ITEMS

def add_or_show_items_choice(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    messages = load_messages(language)
    choice = update.message.text

    if choice == messages["add_item"]:
        update.message.reply_text(messages["lets_add"])
        return language_selection(update, context) 
    elif choice == messages["items"]:
        return show_items(update, context)
    elif choice == messages["settings"]:
        return show_settings_menu(update, context) 
    
def show_settings_menu(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    messages = load_messages(language)
    keyboard = [
        [messages["change_language"]],
        [messages["contact_developer"]],
        [messages["back"]]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    message = update.message.reply_text(messages["settings_menu"], reply_markup=reply_markup)
    context.user_data['settings_menu_message_id'] = message.message_id
    return SETTINGS_MENU

def settings_menu_choice(update: Update, context: CallbackContext) -> int:
    language = context.user_data.get('language', '🇬🇧 English')
    messages = load_messages(language)
    choice = update.message.text

    if choice == messages["change_language"]:
        update.message.reply_text(messages["change_language_prompt"])
    elif choice == messages["contact_developer"]:
        update.message.reply_text(messages["contact_developer_prompt"], parse_mode="HTML")
    elif choice == messages["back"]:
        return add_or_show_items(update, context)
    else:
        update.message.reply_text(messages["invalid_choice"])
        return show_settings_menu(update, context)

def show_items(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    messages = load_messages(language)
    telegram_id = update.message.from_user.id
    
    user_items = session.query(ToriItem).filter_by(telegram_id=telegram_id).all()
    
    if user_items:
        update.message.reply_text(messages["items_list"])
        items_message = ""
        for item in user_items:
            item_info = messages["item"].format(item=item.item)
            item_info += messages["category"].format(category=item.category)
            if item.subcategory != 'null':
                item_info += messages["subcategory"].format(subcategory=item.subcategory)
            if item.product_category != 'null':
                item_info += messages["product_type"].format(product_category=item.product_category)
            item_info += messages["region"].format(region=item.region)
            if item.city != 'null':
                item_info += messages["city"].format(city=item.city)
            if item.area != 'null':
                item_info += messages["area"].format(area=item.area)
            item_info += messages["added_time"].format(time=item.added_time.strftime('%Y-%m-%d %H:%M:%S'))

            remove_button = InlineKeyboardButton(messages["remove_item"], callback_data=str(item.id))
            keyboard = [[remove_button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            items_message += item_info
            update.message.reply_text(items_message, parse_mode="HTML", reply_markup=reply_markup)
            items_message = ""
    else:
        update.message.reply_text(messages["no_items"])
    session.close()
    
    return ADD_OR_SHOW_ITEMS

def remove_item(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    telegram_id = query.from_user.id
    Session = sessionmaker(bind=engine)
    session = Session()
    user_preferences = session.query(UserPreferences).filter_by(telegram_id=telegram_id).first()
    if user_preferences:
        language = user_preferences.language
    else:
        language = '🇬🇧 English'
    messages = load_messages(language)
    query = update.callback_query
    item_id = int(query.data)
    
    item = session.query(ToriItem).filter_by(id=item_id).first()

    if item:
        session.query(ToriItem).filter_by(id=item_id).delete()
        session.commit()
        query.message.reply_text(messages["item_removed"].format(itemname=item.item))
    else:
        query.message.reply_text(messages["item_not_found"])
    session.close()

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Conversation cancelled.")
    return ConversationHandler.END

def check_for_new_items(context: CallbackContext):
    Session = sessionmaker(bind=engine)
    session = Session()

    items = session.query(ToriItem).all()

    for item in items:
        user_preferences = session.query(UserPreferences).filter_by(telegram_id=item.telegram_id).first()
        if user_preferences:
            language = user_preferences.language
        else:
            language = '🇬🇧 English'  
        messages = load_messages(language)

        response = requests.get(item.link)
        if response.status_code != 200:
            continue

        data = response.json()
        new_items = data.get('docs', [])

        if not new_items:
            continue

        latest_time = item.latest_time or item.added_time
        latest_item_time = None

        for ad in new_items:
            timestamp = ad.get('timestamp')
            if timestamp is None:
                continue

            item_time = datetime.fromtimestamp(timestamp / 1000.0)
            if item_time <= latest_time:
                continue

            itemname = ad.get('heading')
            region = ad.get('location')
            canonical_url = ad.get('canonical_url')
            price = ad.get('price', {}).get('amount')
            image_url = ad.get('image', {}).get('url')
            message = messages["new_item"].format(itemname=itemname, region=region, price=price, canonical_url=canonical_url)
            context.bot.send_photo(item.telegram_id, photo=image_url, caption=message, parse_mode="HTML")

            if latest_item_time is None or item_time > latest_item_time:
                latest_item_time = item_time

        if latest_item_time:
            latest_time = latest_item_time
            item.latest_time = latest_time
            session.add(item)
            session.commit()

    session.close()



def main():

    with open('token.txt', encoding="utf-8") as file:
        token = file.read().strip()
    updater = Updater(token, use_context=True)
    job_queue = updater.job_queue

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, start)],
        states={
            SETTINGS_MENU: [MessageHandler(Filters.text & ~Filters.command, settings_menu_choice)],
            LANGUAGE_SELECTION: [MessageHandler(Filters.text & ~Filters.command, language_selection)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_category)],
            SUBCATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_product_category)],
            REGION: [MessageHandler(Filters.text & ~Filters.command, select_region)],
            CITY: [MessageHandler(Filters.text & ~Filters.command, select_city)],
            AREA: [MessageHandler(Filters.text & ~Filters.command, select_area)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, save_data)],
            ADD_OR_SHOW_ITEMS: [MessageHandler(Filters.text & ~Filters.command, add_or_show_items_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('items', show_items))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_item)) 
    updater.dispatcher.add_handler(conv_handler)
    
    job_queue.run_repeating(check_for_new_items, interval=300, first=0)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()