# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import Config

# Create the engine using the URI from config.py
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Create a thread-safe session factory
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # Import all models here so they are registered properly
    import models
    Base.metadata.create_all(bind=engine)