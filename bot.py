import json
import requests 
import pytz
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import DateTime
from datetime import datetime, timezone

engine = create_engine('sqlite:///tori_data.db')
Base = declarative_base()

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

CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA, CONFIRMATION, ADD_OR_SHOW_ITEMS = range(8)

with open('jsons/categories.json', encoding="utf-8") as f:
    categories_data = json.load(f)

with open('jsons/locations.json', encoding="utf-8") as f:
    locations_data = json.load(f)

def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    update.message.reply_text("Please enter the item you're looking for:")
    return CATEGORY

def select_category(update: Update, context: CallbackContext) -> int:
    if 'item' not in context.user_data:
        if not (3 <= len(update.message.text) <= 64):
            update.message.reply_text("Please enter an item name between 3 and 64 characters.")
            return start(update, context)   
        context.user_data['item'] = update.message.text
    keyboard = [[category] for category in categories_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a category:', reply_markup=reply_markup)
    return SUBCATEGORY

def select_subcategory(update: Update, context: CallbackContext) -> int:
    if 'category' not in context.user_data:
        user_category = update.message.text
        if user_category not in categories_data:
            update.message.reply_text("Please select a valid category!")
            return select_category(update, context)
        if user_category.lower() == "kaikki kategoriat":
            context.user_data['category'] = update.message.text
            context.user_data['subcategory'] = 'Kaikki alaluokat'
            return select_region(update, context)
        else:
            context.user_data['category'] = update.message.text

    subcategories = categories_data[context.user_data['category']]["subcategories"]
    keyboard = [[subcategory] for subcategory in subcategories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a subcategory:', reply_markup=reply_markup)
    return PRODUCT_CATEGORY

def select_product_category(update: Update, context: CallbackContext) -> int:
    if 'subcategory' not in context.user_data:
        user_subcategory = update.message.text
        if user_subcategory.lower() != "kaikki kategoriat" and user_subcategory not in categories_data[context.user_data['category']]["subcategories"]:
            update.message.reply_text("Please select a valid subcategory!")
            return select_subcategory(update, context)
        else:
            context.user_data['subcategory'] = update.message.text

    product_categories = categories_data[context.user_data['category']]["subcategories"][context.user_data['subcategory']].get('product_categories')
    if not product_categories:
        context.user_data['product_category'] = 'Kaikki tuoteluokat'
        return select_region(update, context)
    keyboard = [[product_category] for product_category in product_categories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a product type:', reply_markup=reply_markup)
    return REGION

def select_region(update: Update, context: CallbackContext) -> int:
    if 'product_category' not in context.user_data:
        user_product_category = update.message.text
        if user_product_category.lower() != 'kaikki alaluokat' and user_product_category.lower() != 'kaikki kategoriat' and user_product_category not in categories_data[context.user_data['category']]["subcategories"][context.user_data['subcategory']]["product_categories"]:
            update.message.reply_text("Please select a valid product category!")
            return select_product_category(update, context)
        if user_product_category.lower() == "kaikki kategoriat" or user_product_category.lower() == "kaikki alaluokat":
            context.user_data['product_category'] = 'Kaikki tuoteluokat'
        else:
            context.user_data['product_category'] = update.message.text
    
    keyboard = [[region] for region in locations_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a region:', reply_markup=reply_markup)
    return CITY

def select_city(update: Update, context: CallbackContext) -> int:
    
    if 'region' not in context.user_data:
        user_region = update.message.text
        if user_region not in locations_data:
            update.message.reply_text("Please select a valid region!")
            return select_region(update, context)
        if user_region.lower() == "koko suomi":
            context.user_data['region'] = update.message.text
            context.user_data['city'] = 'Kaikki kaupungit'
            context.user_data['area'] = 'Kaikki alueet'
            return save_data(update, context)
        else:
            context.user_data['region'] = update.message.text

    cities = locations_data[context.user_data['region']]["cities"]
    keyboard = [[city] for city in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose an city:', reply_markup=reply_markup)
    return AREA

def select_area(update: Update, context: CallbackContext) -> int:
    if 'city' not in context.user_data:
        user_city = update.message.text
        if user_city.lower() != "koko suomi" and user_city not in locations_data[context.user_data['region']]["cities"]:
            update.message.reply_text("Please select a valid city!")
            return select_city(update, context)
        else:
            context.user_data['city'] = update.message.text

    areas = locations_data[context.user_data['region']]["cities"][context.user_data['city']].get('areas', {})
    if not areas:
        return save_data(update, context)
    keyboard = [[area] for area in areas]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose an area:', reply_markup=reply_markup)
    return CONFIRMATION

def save_data(update: Update, context: CallbackContext) -> int:
    if 'area' not in context.user_data:
        user_area = update.message.text
        if user_area.lower() != "koko suomi" and user_area not in locations_data[context.user_data['region']]["cities"][context.user_data['city']]["areas"]:
            update.message.reply_text("Please select a valid area!")
            return select_area(update, context)
        else:
            context.user_data['area'] = update.message.text

    required_data = ['item', 'category', 'subcategory', 'product_category', 'region', 'city', 'area']
    missing_data = [key for key in required_data if key not in context.user_data]

    if missing_data:
        update.message.reply_text(f"The following data is missing: {', '.join(missing_data)}. Please start over.")
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
        
        Session = sessionmaker(bind=engine)
        session = Session()

        tori_link = f"https://beta.tori.fi/recommerce-search-page/api/search/SEARCH_ID_BAP_COMMON?q={item.lower()}"
        if category.lower() != 'kaikki kategoriat':
            if subcategory.lower() != 'kaikki alaluokat':
                if product_category.lower()!= 'kaikki tuoteluokat':
                    product_category_code = categories_data[category]["subcategories"][subcategory]["product_categories"][product_category]
                    tori_link += f"&product_category={product_category_code}"
                else:
                    subcategory_code = categories_data[category]["subcategories"][subcategory]["subcategory_code"]
                    tori_link += f"&sub_category={subcategory_code}"
            else:
                category_code = categories_data[category]["category_code"]
                tori_link += f"&category={category_code}"
        if region.lower() != 'koko suomi':
            if city.lower() != 'kaikki kaupungit':
                if area.lower() != 'kaikki alueet':
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

        message = f"A new item was added!\nItem: {item}\nCategory: {category}\n"
        if subcategory.lower() != 'kaikki alaluokat':
            message += f"Subcategory: {subcategory}\n"
        if product_category.lower() != 'kaikki tuoteluokat':
            message += f"Product type: {product_category}\n"
        message += f"Region: {region}\n"
        if city.lower() != 'kaikki kaupungit':
            message += f"City: {city}\n"
        if area.lower() != 'kaikki alueet':
            message += f"Area: {area}\n"
        message += f"Added Time: {new_item.added_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        update.message.reply_text(message + f"The search link for the item: {tori_link}", reply_markup=ReplyKeyboardMarkup([['Add a new item', 'Items']], one_time_keyboard=True))
        
        session.close()
        
        return ADD_OR_SHOW_ITEMS

def add_or_show_items(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    
    if choice == 'Add a new item':
        update.message.reply_text("Let's add a new item.")
        return start(update, context) 
    elif choice == 'Items':
        return show_items(update, context)


def show_items(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    
    Session = sessionmaker(bind=engine)
    session = Session()
    user_items = session.query(ToriItem).filter_by(telegram_id=telegram_id).all()
    
    if user_items:
        update.message.reply_text("Here are the items you're currently looking for:")
        items_message = ""
        for item in user_items:
            item_info = f"Item: {item.item}\nCategory: {item.category}\n"
            if item.subcategory != 'null':
                item_info += f"Subcategory: {item.subcategory}\n"
            item_info += f"Region: {item.region}\n"
            if item.city != 'null':
                item_info += f"City: {item.city}\n"
            item_info += f"Added Time: {item.added_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            remove_button = InlineKeyboardButton("Remove item", callback_data=str(item.id))
            keyboard = [[remove_button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            items_message += item_info
            update.message.reply_text(items_message, reply_markup=reply_markup)
            items_message = ""
    else:
        update.message.reply_text("You haven't added any items yet.")
    session.close()
    
    return ADD_OR_SHOW_ITEMS

def remove_item(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    item_id = int(query.data)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    item = session.query(ToriItem).filter_by(id=item_id).first()

    if item:
        session.query(ToriItem).filter_by(id=item_id).delete()
        session.commit()
        query.message.reply_text(f"{item.item} was successfully removed!")
    else:
        query.message.reply_text("Item not found!")
    session.close()

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Conversation cancelled.")
    return ConversationHandler.END

def check_for_new_items(context: CallbackContext):
    Session = sessionmaker(bind=engine)
    session = Session()

    items = session.query(ToriItem).all()

    for item in items:
        response = requests.get(item.link)
        if response.status_code != 200:
            continue

        data = response.json()
        new_items = data.get('docs', [])

        if not new_items:
            continue

        latest_time = item.latest_time or item.added_time
        for i, ad in enumerate(new_items):
            timestamp = ad.get('timestamp')
            if timestamp is None:
                continue

            item_time = datetime.fromtimestamp(timestamp / 1000.0)
            if item_time <= latest_time:
                break

            region = ad.get('location')
            canonical_url = ad.get('canonical_url')
            price = ad.get('price', {}).get('value')
            trade_type = ad.get('trade_type')
            message = f"New item found: {ad.get('heading')}\nRegion: {region}\nPrice: {price} EUR\nTrade Type: {trade_type}\n{canonical_url}"

            context.bot.send_message(item.telegram_id, message)
            latest_time = item_time

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
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_category)],
            SUBCATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_subcategory)],
            PRODUCT_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, select_product_category)],
            REGION: [MessageHandler(Filters.text & ~Filters.command, select_region)],
            CITY: [MessageHandler(Filters.text & ~Filters.command, select_city)],
            AREA: [MessageHandler(Filters.text & ~Filters.command, select_area)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, save_data)],
            ADD_OR_SHOW_ITEMS: [MessageHandler(Filters.text & ~Filters.command, add_or_show_items)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('items', show_items))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_item)) 
    updater.dispatcher.add_handler(conv_handler)
    
    job_queue.run_repeating(check_for_new_items, interval=60, first=0)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()