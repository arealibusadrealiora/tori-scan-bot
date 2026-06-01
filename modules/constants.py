import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Admin settings
ADMIN_ID = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None

# Conversation states
(LANGUAGE, ITEM, CATEGORY, SUBCATEGORY, PRODUCT_CATEGORY, REGION, CITY, AREA,
 MORE_LOCATIONS, MORE_CATEGORIES, ADDITIONAL_FILTERS, DEALER_SEGMENT,
 SHIPPING_TYPES, PRICE_FROM, PRICE_TO, MAIN_MENU, SETTINGS_MENU, CONFIRMATION,
 ADMIN_MENU, ADMIN_BROADCAST_SELECT_LANGUAGE, ADMIN_BROADCAST_MESSAGE,
 ADMIN_BROADCAST_CONFIRM) = range(22)

# Other constants
ALL_CATEGORIES = ['kaikki kategoriat', 'all categories', 'все категории', 'всі категорії']
ALL_SUBCATEGORIES = ['kaikki alaluokat', 'all subcategories', 'все подкатегории', 'всі підкатегорії']
ALL_PRODUCT_CATEGORIES = ['kaikki tuoteluokat', 'all product categories', 'все категории товаров', 'всі категорії товарів']
WHOLE_FINLAND = ['koko suomi', 'whole finland', 'вся финляндия', 'вся фінляндія']
ALL_CITIES = ['kaikki kaupungit', 'all cities', 'все города', 'всі міста']
ALL_AREAS = ['kaikki alueet', 'all areas', 'все области', 'всі райони']