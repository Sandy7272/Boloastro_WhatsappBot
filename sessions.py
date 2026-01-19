# sessions.py
from database import db_session
from models import BotSession, User
import logging

logger = logging.getLogger(__name__)

DEFAULT_SESSION_DATA = {
    "stage": "LANG",
    "language": "en",
    "details": {},
    "chart": None,
    "dasha": None,
    "ready": False
}

def get_session(phone_number):
    """
    Retrieves the user's session data from the DB.
    If no session exists, creates a new one.
    """
    try:
        # 1. Ensure User exists in the User table (for tracking tier/questions)
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db_session.add(user)
            db_session.commit()

        # 2. Get Session State
        session_row = BotSession.query.filter_by(phone_number=phone_number).first()
        
        if not session_row:
            # Create new session entry
            session_row = BotSession(phone_number=phone_number, data=DEFAULT_SESSION_DATA)
            db_session.add(session_row)
            db_session.commit()
            return session_row.data.copy() # Return a mutable dict copy
        
        # Merge defaults if missing keys (e.g. after code update)
        data = session_row.data
        if not data: 
            data = DEFAULT_SESSION_DATA
            
        return data

    except Exception as e:
        logger.error(f"DB Error in get_session: {e}")
        db_session.rollback()
        return DEFAULT_SESSION_DATA.copy()

def save_session(phone_number, new_data):
    """
    Saves the updated dictionary back to the JSON column in DB.
    MUST be called at the end of the request in app.py.
    """
    try:
        session_row = BotSession.query.filter_by(phone_number=phone_number).first()
        if session_row:
            # SQLAlchemy tracks changes to JSON objects differently, 
            # so we explicitly reassign it to trigger an update.
            session_row.data = new_data
            db_session.commit()
    except Exception as e:
        logger.error(f"DB Error in save_session: {e}")
        db_session.rollback()