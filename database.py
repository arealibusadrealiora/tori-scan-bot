from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine('sqlite:///tori_data.db')

def get_session():
    '''
    Create and return a new SQLAlchemy session.
    Returns:
        Session: A new SQLAlchemy session.
    '''
    Session = sessionmaker(bind=engine)
    return Session()

# Create the database tables
Base.metadata.create_all(engine)
