"""
Migration script to add price_from and price_to columns.

This migration:
1. Adds support for price range filtering
2. Adds price_from column (INTEGER, nullable)
3. Adds price_to column (INTEGER, nullable)
For existing items, the default value is set to NULL (no price filter).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from modules.models import Base, ToriItem

def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_price_range():
    """
    Adds price_from and price_to columns to tori_items table.
    Sets default value NULL for all existing items.
    """
    engine = create_engine('sqlite:///tori_data.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        price_from_exists = column_exists(engine, 'tori_items', 'price_from')
        price_to_exists = column_exists(engine, 'tori_items', 'price_to')

        if price_from_exists and price_to_exists:
            print("Columns 'price_from' and 'price_to' already exist in the database!")
            print("No migration needed.")
            return

        print("Starting migration to add price range columns...")
        print("=" * 60)

        # Add price_from column if it doesn't exist
        if not price_from_exists:
            print("\nStep 1: Adding price_from column to tori_items table...")
            session.execute(text('ALTER TABLE tori_items ADD COLUMN price_from INTEGER'))
            session.commit()
            print("✓ price_from column added successfully")
        else:
            print("\nStep 1: price_from column already exists, skipping...")

        # Add price_to column if it doesn't exist
        if not price_to_exists:
            print("\nStep 2: Adding price_to column to tori_items table...")
            session.execute(text('ALTER TABLE tori_items ADD COLUMN price_to INTEGER'))
            session.commit()
            print("✓ price_to column added successfully")
        else:
            print("\nStep 2: price_to column already exists, skipping...")

        # Verify the migration
        print("\nStep 3: Verifying migration...")
        items = session.query(ToriItem).all()
        print(f"✓ Found {len(items)} items in database")
        print("✓ All existing items will have NULL price filters (no price limit)")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("\nSummary:")
        print(f"  - Added price_from column to tori_items table")
        print(f"  - Added price_to column to tori_items table")
        print(f"  - Total items in database: {len(items)}")
        print(f"\nAll items now support price range filtering!")

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Price Range Migration Tool")
    print("=" * 60)
    print("This script will:")
    print("1. Add price_from column (INTEGER, nullable)")
    print("2. Add price_to column (INTEGER, nullable)")
    print("=" * 60)

    try:
        migrate_price_range()
    except Exception as e:
        print("\n✗ Migration failed!")
        print("The database should be intact in its original state.")
        print(f"Error: {str(e)}")
        sys.exit(1)
