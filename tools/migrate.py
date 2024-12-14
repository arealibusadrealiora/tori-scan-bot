from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, MetaData, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import logging

# This script migrates old database (the one without the support of multiple locations/categories) to a new format

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///tori_data.db')
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class OldToriItem(Base):
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

class NewToriItem(Base):
    __tablename__ = 'new_tori_items'
    id = Column(Integer, primary_key=True)
    item = Column(String)
    categories = Column(JSON)
    locations = Column(JSON)
    telegram_id = Column(Integer)
    added_time = Column(DateTime, default=datetime.now)
    link = Column(String)
    latest_time = Column(DateTime)

def check_table_exists(table_name):
    meta = MetaData()
    meta.reflect(bind=engine)
    return table_name in meta.tables

def migrate_database():
    logger.info("Starting database migration...")
    
    if not check_table_exists('tori_items'):
        logger.error("Old table 'tori_items' does not exist!")
        return
    
    try:
        if not check_table_exists('new_tori_items'):
            logger.info("Creating new_tori_items table...")
            NewToriItem.__table__.create(engine)
        
        logger.info("Loading items from old format...")
        old_items = session.query(OldToriItem).all()
        logger.info(f"Found {len(old_items)} items to migrate")
        
        for old_item in old_items:
            logger.info(f"Migrating item: {old_item.item}")
            categories = [{
                'category': str(old_item.category) if old_item.category is not None else None,
                'subcategory': str(old_item.subcategory) if old_item.subcategory is not None else None,
                'product_category': str(old_item.product_category) if old_item.product_category is not None else None
            }]
            
            locations = [{
                'region': str(old_item.region) if old_item.region is not None else None,
                'city': str(old_item.city) if old_item.city is not None else None,
                'area': str(old_item.area) if old_item.area is not None else None
            }]
            
            new_item = NewToriItem(
                item=old_item.item,
                categories=categories,
                locations=locations,
                telegram_id=old_item.telegram_id,
                added_time=old_item.added_time,
                link=old_item.link,
                latest_time=old_item.latest_time
            )
            
            session.add(new_item)
        
        logger.info("Committing changes...")
        session.commit()
        
        logger.info("Creating backup of old table...")
        session.execute(text('ALTER TABLE tori_items RENAME TO tori_items_backup;'))
        session.commit()
        
        logger.info("Renaming new table...")
        session.execute(text('ALTER TABLE new_tori_items RENAME TO tori_items;'))
        session.commit()
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error during migration: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print("\nMigration failed! The database should be intact in its original state.")
        print("Please check the error messages above for details.")
    else:
        print("\nMigration completed successfully!")
        print("The old data has been backed up in 'tori_items_backup' table.")
        print("The new table structure is now in place with all data migrated.")