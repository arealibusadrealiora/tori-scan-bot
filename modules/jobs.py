import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from modules.load import load_messages
from modules.models import ToriItem
from modules.database import get_session
from modules.utils import get_language

async def check_for_new_items(context: ContextTypes.DEFAULT_TYPE):
    '''
    Check for new items on the external API and notify the user if there are any.
    Args:
        context (ContextTypes.DEFAULT_TYPE): The context object for accessing bot and job queue.
    '''
    session = get_session()
    try:
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
                
                try:
                    if image_url:
                        await context.bot.send_photo(item.telegram_id, photo=image_url, caption=message, parse_mode='HTML')
                    else:
                        await context.bot.send_message(item.telegram_id, text=message, parse_mode='HTML')
                except Forbidden:
                    print(f"User {item.telegram_id} has blocked the bot. Removing their items from the database.")
                    session.query(ToriItem).filter_by(telegram_id=item.telegram_id).delete()
                    session.commit()
                    break
                except BadRequest as e:
                    print(f"Bad request for user {item.telegram_id}: {e}")
                    continue
                except Exception as e:
                    print(f"Unexpected error for user {item.telegram_id}: {e}")
                    continue

                if latest_item_time is None or item_time > latest_item_time:
                    latest_item_time = item_time

            if latest_item_time:
                latest_time = latest_item_time
                item.latest_time = latest_time
                session.add(item)
                session.commit()
    
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
    finally:
        session.close()
    session.close()

def setup_jobs(job_queue):
    '''
    Schedules the job to check for new items at regular intervals.
    Args:
        job_queue: The job queue to which the job should be added.
    '''
    async def wrapper(context):
        await check_for_new_items(context)
    # interval is in seconds; 300 seconds = 5 minutes; please don't put it lower than thst, it's pointless.
    job_queue.run_repeating(check_for_new_items, interval=300, first=0)
