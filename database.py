import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trend_miner.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    current_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    type = Column(String)  # 'buy', 'sell', 'deposit', 'withdraw'
    symbol = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    price = Column(Float)
    amount = Column(Float)
    status = Column(String, default="pending")  # 'pending', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)

class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    trend_score = Column(Float)
    recommendation = Column(String)  # 'buy', 'sell', 'hold'
    confidence = Column(Float)
    analysis_data = Column(Text)  # JSON string with detailed analysis
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    risk_tolerance = Column(String, default="medium")  # 'low', 'medium', 'high'
    investment_amount = Column(Float, default=100.0)
    auto_invest = Column(Boolean, default=False)
    preferred_sectors = Column(Text)  # JSON list of sectors
    preferred_symbols = Column(Text)  # JSON list of symbols
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)