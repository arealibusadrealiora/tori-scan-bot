import json
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

Base.metadata.create_all(engine)

CATEGORY, SUBCATEGORY, REGION, AREA, CONFIRMATION, ADD_OR_SHOW_ITEMS = range(6)

with open('jsons/categories.json') as f:
    categories_data = json.load(f)

with open('jsons/location.json') as f:
    locations_data = json.load(f)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Please enter the item you're looking for:")
    return CATEGORY

def select_category(update: Update, context: CallbackContext) -> int:
    context.user_data['item'] = update.message.text
    keyboard = [[category for category in categories_data]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a category:', reply_markup=reply_markup)
    return SUBCATEGORY

def select_subcategory(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text
    user_category = update.message.text

    if user_category.lower() == "kaikki kategoriat":
        return select_region(update, context)

    subcategories = categories_data[user_category]["subcategories"]
    keyboard = [[subcategory for subcategory in subcategories]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a subcategory:', reply_markup=reply_markup)
    return REGION

def select_region(update: Update, context: CallbackContext) -> int:
    context.user_data['subcategory'] = update.message.text
    user_subcategory = update.message.text

    if user_subcategory.lower() == "kaikki kategoriat":
        context.user_data['subcategory'] = 'null'
    
    keyboard = [[region for region in locations_data]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a region:', reply_markup=reply_markup)
    return AREA

def select_area(update: Update, context: CallbackContext) -> int:
    context.user_data['region'] = update.message.text
    user_region = update.message.text

    if user_region.lower() == "koko suomi":
        return save_data(update, context)

    areas = locations_data[user_region]["areas"]
    keyboard = [[area for area in areas]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose an area:', reply_markup=reply_markup)
    return CONFIRMATION

def save_data(update: Update, context: CallbackContext) -> int:
    context.user_data['area'] = update.message.text
    user_area = update.message.text

    if user_area.lower() == "koko suomi":
        context.user_data['area'] = 'null'

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
        
        new_item = ToriItem(item=item, category=category, subcategory=subcategory, region=region, area=area, telegram_id=telegram_id)
        
        session.add(new_item)
        session.commit()

        message = f"A new item was added!\nItem: {item}\nCategory: {category}\n"
        if subcategory != 'null':
            message += "Subcategory: {subcategory}\n"
        message += f"Region: {region}\n"
        if area != 'null':
            message += "Area: {area}"
        
        update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup([['Add a new item', 'Items']], one_time_keyboard=True))
        
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
            item_info += f"Region: {item.region}\nArea: {item.area}\n\n"
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

def main():
    updater = Updater("token", use_context=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
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

    updater.dispatcher.add_handler(CommandHandler('items', show_items))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_item)) 
    updater.dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
