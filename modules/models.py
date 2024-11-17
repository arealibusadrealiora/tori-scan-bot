from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON

Base = declarative_base()

class UserPreferences(Base):
    '''
    SQLAlchemy model for user preferences.
    Attributes:
        id (int): Primary key.
        telegram_id (int): The user's Telegram ID.
        language (str): Preferred language of the user.
    '''
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    language = Column(String)

class ToriItem(Base):
    '''
    SQLAlchemy model for items tracked on Tori.fi.
    Attributes:
        id (int): Primary key.
        item (str): Name of the item.
        category (int): Category ID.
        subcategory (int): Subcategory ID.
        product_category (int): Product category ID.
        region (int): Region ID.
        city (int): City ID.
        area (int): Area ID.
        telegram_id (int): The user's Telegram ID.
        added_time (datetime): Time when the item was added.
        link (str): URL link to the item on Tori.fi.
        latest_time (datetime): Latest time the item was checked.
    '''
    __tablename__ = 'tori_items'

    id = Column(Integer, primary_key=True)
    item = Column(String)
    category = Column(Integer)
    subcategory = Column(Integer)
    product_category = Column(Integer)
    locations = Column(JSON)
    telegram_id = Column(Integer)
    added_time = Column(DateTime, default=datetime.now)
    link = Column(String)
    latest_time = Column(DateTime)