"""
Migration script to update tori.fi API URLs in the database
from old format to new format.

Old: https://www.tori.fi/recommerce-search-page/api/search/
New: https://www.tori.fi/recommerce/forsale/search/api/search/
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ToriItem

def migrate_urls():
    """
    Updates all existing tori.fi URLs in the database to use the new API endpoint.
    """
    engine = create_engine('sqlite:///tori_data.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    old_url_pattern = 'https://www.tori.fi/recommerce-search-page/api/search/'
    new_url_pattern = 'https://www.tori.fi/recommerce/forsale/search/api/search/'
    
    try:
        items = session.query(ToriItem).all()
        updated_count = 0
        
        print(f"Found {len(items)} items in the database")
        
        for item in items:
            if item.link and old_url_pattern in item.link:
                old_link = item.link
                item.link = item.link.replace(old_url_pattern, new_url_pattern)
                updated_count += 1
                
                print(f"Updated item ID {item.id}:")
                print(f"  Old: {old_link}")
                print(f"  New: {item.link}")
        
        if updated_count > 0:
            session.commit()
            print(f"\nSuccessfully updated {updated_count} URLs")
        else:
            print("\nNo URLs needed updating (all URLs are already in the new format)")
            
    except Exception as e:
        print(f"\nError during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting URL migration...")
    print("=" * 50)
    migrate_urls()
    print("=" * 50)
    print("Migration completed!")