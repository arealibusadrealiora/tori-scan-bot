"""
Migration script to add dealer_segments column to tori_items table.

This migration adds support for filtering by seller type (yksityinen/yritys).
For existing items, the default value is set to both types (all sellers).
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

def migrate_dealer_segments():
    """
    Adds dealer_segments column to tori_items table.
    Sets default value ['yksityinen', 'yritys'] for all existing items.
    """
    engine = create_engine('sqlite:///tori_data.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if column already exists
        if column_exists(engine, 'tori_items', 'dealer_segments'):
            print("Column 'dealer_segments' already exists in the database!")
            print("No migration needed.")
            return

        print("Starting migration to add dealer_segments column...")
        print("=" * 60)

        # Add the new column (SQLite doesn't support adding JSON columns with ALTER TABLE directly)
        # We need to use a workaround for SQLite
        print("\nStep 1: Adding dealer_segments column to tori_items table...")

        # For SQLite, we need to add a TEXT column and will store JSON as text
        session.execute(text('ALTER TABLE tori_items ADD COLUMN dealer_segments TEXT'))
        session.commit()
        print("✓ Column added successfully")

        # Get all items
        print("\nStep 2: Updating existing items with default value...")
        items = session.query(ToriItem).all()
        print(f"Found {len(items)} items to update")

        # Set default value for all existing items
        default_value = ['yksityinen', 'yritys']
        updated_count = 0

        for item in items:
            if item.dealer_segments is None:
                item.dealer_segments = default_value
                updated_count += 1

        if updated_count > 0:
            session.commit()
            print(f"✓ Updated {updated_count} items with default dealer_segments")
        else:
            print("✓ No items needed updating")

        # Update URLs to include dealer_segment parameters
        print("\nStep 3: Updating URLs with dealer_segment parameters...")
        items = session.query(ToriItem).all()
        url_updated_count = 0

        for item in items:
            if item.link and '&dealer_segment=' not in item.link:
                # Add dealer_segment parameters before &sort=
                if '&sort=' in item.link:
                    base_url = item.link.split('&sort=')[0]
                    sort_param = '&sort=' + item.link.split('&sort=')[1]

                    # Add dealer segments (только если выбран один конкретный тип)
                    dealer_params = ''
                    segments = item.dealer_segments if item.dealer_segments else ['yksityinen', 'yritys']

                    # Добавляем параметр только если выбран один тип продавца
                    if len(segments) == 1:
                        if segments[0] == 'yksityinen':
                            dealer_params = '&dealer_segment=1'
                        elif segments[0] == 'yritys':
                            dealer_params = '&dealer_segment=3'
                    # Если выбраны оба - не добавляем параметр (пустая строка)

                    item.link = base_url + dealer_params + sort_param
                    url_updated_count += 1

        if url_updated_count > 0:
            session.commit()
            print(f"✓ Updated {url_updated_count} URLs with dealer_segment parameters")
        else:
            print("✓ No URLs needed updating")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("\nSummary:")
        print(f"  - Added dealer_segments column to tori_items table")
        print(f"  - Updated {updated_count} existing items with default value")
        print(f"  - Updated {url_updated_count} URLs with dealer_segment parameters")
        print(f"\nAll items now support filtering by seller type (yksityinen/yritys)")

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Dealer Segments Migration Tool")
    print("=" * 60)
    print("This script will add support for seller type filtering.")
    print("=" * 60)

    try:
        migrate_dealer_segments()
    except Exception as e:
        print("\n✗ Migration failed!")
        print("The database should be intact in its original state.")
        print(f"Error: {str(e)}")
        sys.exit(1)
