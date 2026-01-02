"""
Check script to verify the status of URLs in the ToriScan database.
Run this before and after migration to confirm the changes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ToriItem
from collections import Counter

def check_database_urls():
    """Check and report on the URLs in the database."""
    
    engine = create_engine('sqlite:///tori_data.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        items = session.query(ToriItem).all()
        
        if not items:
            print("No items found in the database!")
            return
        
        old_url_pattern = 'recommerce-search-page'
        new_url_pattern = 'recommerce/forsale/search'
        
        old_urls = []
        new_urls = []
        invalid_urls = []
        
        for item in items:
            if not item.link:
                invalid_urls.append(item)
            elif old_url_pattern in item.link:
                old_urls.append(item)
            elif new_url_pattern in item.link:
                new_urls.append(item)
            else:
                invalid_urls.append(item)
        
        print("=" * 60)
        print("ToriScan Database URL Status Report")
        print("=" * 60)
        print(f"Total items in database: {len(items)}")
        print("-" * 60)
        
        if old_urls:
            print(f"Items with OLD URL format: {len(old_urls)}")
            print("   These need migration!")
            print("   Sample items:")
            for item in old_urls[:3]:
                print(f"   - ID {item.id}: {item.item}")
        else:
            print("No items with old URL format found")
        
        if new_urls:
            print(f"Items with NEW URL format: {len(new_urls)}")
            print("   Sample items:")
            for item in new_urls[:3]:
                print(f"   - ID {item.id}: {item.item}")
        else:
            print("No items with new URL format found")
        
        if invalid_urls:
            print(f"Items with invalid/missing URLs: {len(invalid_urls)}")
            for item in invalid_urls[:3]:
                print(f"   - ID {item.id}: {item.item}")
        
        print("-" * 60)
        
        if old_urls:
            print("\nACTION REQUIRED:")
            print(f"   You need to migrate {len(old_urls)} items to the new URL format.")
            print("   Run: python migrate_urls.py")
        elif new_urls and not old_urls:
            print("\nDATABASE STATUS: All URLs are up to date!")
        else:
            print("\nDATABASE STATUS: Check your database configuration")
        
        print("=" * 60)
        
        if items:
            print("\nSample URLs in database:")
            for item in items[:2]:
                if item.link:
                    print(f"\nItem: {item.item}")
                    print(f"URL: {item.link[:100]}...")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database_urls()