"""定义表结构"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base  # 从刚才写的 database.py 导入 Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="user") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ratings = relationship("Rating", back_populates="user")

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), index=True, nullable=False)
    genres = Column(String(100))
    emotion_tags = Column(String(100))
    director = Column(String(100)) 
    cast = Column(String(255)) 
    description = Column(Text) 
    cover_url = Column(String(255))
    average_rating = Column(Float, default=0.0) 
    
    ratings = relationship("Rating", back_populates="movie")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    score = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")