import requests
from telegram.ext import CallbackContext
from datetime import datetime
from load import load_messages
from models import ToriItem
from database import get_session
from utils import get_language

def check_for_new_items(context: CallbackContext):
    '''
    Check for new items on the external API and notify the user if there are any.
    Args:
        context (CallbackContext): The context object for accessing bot and job queue.
    '''
    session = get_session()
    items = session.query(ToriItem).all()
    for item in items:
        telegram_id = item.telegram_id
        language = get_language(telegram_id)
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
            message = messages['new_item'].format(itemname=itemname, region=region, price=price, canonical_url=canonical_url)
            context.bot.send_photo(item.telegram_id, photo=image_url, caption=message, parse_mode='HTML')

            if latest_item_time is None or item_time > latest_item_time:
                latest_item_time = item_time

        if latest_item_time:
            latest_time = latest_item_time
            item.latest_time = latest_time
            session.add(item)
            session.commit()

    session.close()

def setup_jobs(job_queue):
    job_queue.run_repeating(check_for_new_items, interval=300, first=0)