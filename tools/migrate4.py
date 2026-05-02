"""
Migration script to add shipping_types column and update API URL.

This migration:
1. Adds support for ToriDiili shipping filter
2. Updates API endpoint from /api/search/ to /api/pole-position/
For existing items, the default value is set to ['all'] (all items).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from modules.models import Base, ToriItem
import json

def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_shipping_types():
    """
    Adds shipping_types column to tori_items table and updates API URLs.
    Sets default value ['all'] for all existing items.
    Updates API endpoint from /api/search/ to /api/pole-position/.
    """
    engine = create_engine('sqlite:///tori_data.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if column already exists
        if column_exists(engine, 'tori_items', 'shipping_types'):
            print("Column 'shipping_types' already exists in the database!")
            print("No migration needed for column creation.")
        else:
            print("Starting migration to add shipping_types column...")
            print("=" * 60)

            # Add the new column (SQLite doesn't support adding JSON columns with ALTER TABLE directly)
            # We need to use a workaround for SQLite
            print("\nStep 1: Adding shipping_types column to tori_items table...")

            # For SQLite, we need to add a TEXT column and will store JSON as text
            session.execute(text('ALTER TABLE tori_items ADD COLUMN shipping_types TEXT'))
            session.commit()
            print("✓ Column added successfully")

            # Get all items
            print("\nStep 2: Updating existing items with default value...")
            items = session.query(ToriItem).all()
            print(f"Found {len(items)} items to update")

            # Set default value for all existing items
            default_value = ['all']
            updated_count = 0

            for item in items:
                if item.shipping_types is None:
                    item.shipping_types = default_value
                    updated_count += 1

            if updated_count > 0:
                session.commit()
                print(f"✓ Updated {updated_count} items with default shipping_types")
            else:
                print("✓ No items needed updating")

        # Update URLs from old API endpoint to new one
        print("\nStep 3: Updating API URLs from /api/search/ to /api/pole-position/...")
        items = session.query(ToriItem).all()
        url_updated_count = 0

        old_api_path = '/api/search/'
        new_api_path = '/api/pole-position/'

        for item in items:
            if item.link and old_api_path in item.link:
                item.link = item.link.replace(old_api_path, new_api_path)
                url_updated_count += 1

        if url_updated_count > 0:
            session.commit()
            print(f"✓ Updated {url_updated_count} URLs to new API endpoint")
        else:
            print("✓ All URLs are already using the new API endpoint")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("\nSummary:")
        print(f"  - Added shipping_types column to tori_items table (if needed)")
        print(f"  - Updated existing items with default value ['all']")
        print(f"  - Updated {url_updated_count} URLs to new API endpoint")
        print(f"\nAll items now support ToriDiili shipping filter")

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Shipping Types & API URL Migration Tool")
    print("=" * 60)
    print("This script will:")
    print("1. Add shipping_types column (if not exists)")
    print("2. Update API endpoint to /api/pole-position/")
    print("=" * 60)

    try:
        migrate_shipping_types()
    except Exception as e:
        print("\n✗ Migration failed!")
        print("The database should be intact in its original state.")
        print(f"Error: {str(e)}")
        sys.exit(1)