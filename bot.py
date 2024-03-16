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
    region = Column(Integer)
    area = Column(Integer)
    telegram_id = Column(Integer)
    added_time = Column(DateTime, default=datetime.now)
    link = Column(String)
    latest_time = Column(DateTime) 

Base.metadata.create_all(engine)

CATEGORY, SUBCATEGORY, REGION, AREA, CONFIRMATION, ADD_OR_SHOW_ITEMS = range(6)

with open('jsons/categories.json', encoding="utf-8") as f:
    categories_data = json.load(f)

with open('jsons/location.json', encoding="utf-8") as f:
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
            return select_region(update, context)
        else:
            context.user_data['category'] = update.message.text

    subcategories = categories_data[context.user_data['category']]["subcategories"]
    keyboard = [[subcategory] for subcategory in subcategories]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a subcategory:', reply_markup=reply_markup)
    return REGION

def select_region(update: Update, context: CallbackContext) -> int:
    user_category = context.user_data.get('category')  
    if 'subcategory' not in context.user_data:
        user_subcategory = update.message.text
        if user_subcategory.lower() != "kaikki kategoriat" and user_subcategory not in categories_data[user_category]["subcategories"]:
            update.message.reply_text("Please select a valid subcategory!")
            return select_subcategory(update, context)
        if user_subcategory.lower() == "kaikki kategoriat":
            context.user_data['subcategory'] = 'null'
        else:
            context.user_data['subcategory'] = update.message.text
    
    keyboard = [[region] for region in locations_data]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a region:', reply_markup=reply_markup)
    return AREA

def select_area(update: Update, context: CallbackContext) -> int:
    
    if 'region' not in context.user_data:
        user_region = update.message.text
        if user_region not in locations_data:
            update.message.reply_text("Please select a valid region!")
            return select_region(update, context)
        if user_region.lower() == "koko suomi":
            context.user_data['region'] = update.message.text
            return save_data(update, context)
        else:
            context.user_data['region'] = update.message.text

    areas = locations_data[context.user_data['region']]["areas"]
    keyboard = [[area] for area in areas]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose an area:', reply_markup=reply_markup)
    return CONFIRMATION

def save_data(update: Update, context: CallbackContext) -> int:
    user_region = context.user_data.get('region')  
    if 'area' not in context.user_data:
        user_area = update.message.text
        if user_area.lower() != "koko suomi" and user_area not in locations_data[user_region]["areas"]:
            update.message.reply_text("Please select a valid area!")
            return select_area(update, context)
        if user_area.lower() == "koko suomi":
            context.user_data['area'] = 'null'
        else:
            context.user_data['area'] = update.message.text

    required_data = ['item', 'category', 'subcategory', 'region', 'area']
    missing_data = [key for key in required_data if key not in context.user_data]

    if missing_data:
        update.message.reply_text(f"The following data is missing: {', '.join(missing_data)}. Please start over.")
        return ConversationHandler.END
    else:
        item = context.user_data['item']
        category = context.user_data['category']
        subcategory = context.user_data['subcategory']
        region = context.user_data['region']
        area = context.user_data['area']
        
        telegram_id = update.message.from_user.id
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        if category.lower() != 'kaikki kategoriat':
            subcategory_code = categories_data[category]["subcategories"][subcategory]
        if region.lower() != 'koko suomi':
            region_code = locations_data[region]["region_code"]
            area_code = locations_data[region]["areas"][area]

        tori_link = f"https://api.tori.fi/api/v2/listings/search?ad_type=s&q={item.lower()}"
        if category.lower() != 'kaikki kategoriat':
            tori_link += f"&category={subcategory_code}%2C330"
        if region.lower() != 'koko suomi':
            if area != 'null':
                tori_link += f"&municipality={area_code}%2C330"
            tori_link += f"&region={region_code}%2C18"
        tori_link += "&suborder=0-1000"

        new_item = ToriItem(item=item, category=category, subcategory=subcategory, region=region, area=area, telegram_id=telegram_id, link=tori_link)
        
        session.add(new_item)
        session.commit()

        message = f"A new item was added!\nItem: {item}\nCategory: {category}\n"
        if subcategory != 'null':
            message += f"Subcategory: {subcategory}\n"
        message += f"Region: {region}\n"
        if area != 'null':
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
            if item.area != 'null':
                item_info += f"Area: {item.area}\n"
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
        if response.status_code == 200:
            data = response.json()
            latest_time = item.latest_time or item.added_time
            latest_time = latest_time.astimezone(pytz.timezone('Europe/Helsinki'))
            
            latest_list_time = None 

            for ad in data['list_ads']:
                list_time = datetime.strptime(ad['ad']['list_time'], "%Y-%m-%dT%H:%M:%S%z")
                list_time = list_time.astimezone(pytz.timezone('Europe/Helsinki'))
                if list_time > latest_time:

                    list_id_code = ad['ad']['list_id_code']
                    region_label = ad['ad']['location']['region']['label']
                    tori_link = f"https://www.tori.fi/{region_label.lower()}/{list_id_code}.htm"
                    message = f"New item found: {ad['ad']['subject']}\n{tori_link}"
                    context.bot.send_message(item.telegram_id, message)
                    if latest_list_time is None or list_time > latest_list_time:
                        latest_list_time = list_time  

            if latest_list_time is not None:
                latest_time_str = latest_list_time.strftime("%Y-%m-%d %H:%M:%S")
                item.latest_time = datetime.strptime(latest_time_str, "%Y-%m-%d %H:%M:%S")
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
            REGION: [MessageHandler(Filters.text & ~Filters.command, select_region)],
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