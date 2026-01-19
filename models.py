# models.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    
    phone_number = Column(String(20), primary_key=True)
    tier = Column(String(10), default="free")  # 'free' or 'vip'
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    questions_left = Column(Integer, default=2)
    
    def __repr__(self):
        return f"<User {self.phone_number}>"

class BotSession(Base):
    __tablename__ = 'sessions'
    
    phone_number = Column(String(20), primary_key=True)
    
    # We store the entire session dictionary (details, stage, etc.) as JSON
    # This means you don't have to change your logic in app.py much!
    data = Column(JSON, default={}) 
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Session {self.phone_number}>"