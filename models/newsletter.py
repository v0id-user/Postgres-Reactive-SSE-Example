"""Newsletter models for database and API."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from pydantic import BaseModel
from database.config import Base

# SQLAlchemy Model
class Newsletter(Base):
    """Database model for newsletters."""
    __tablename__ = "newsletters"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API
class NewsletterCreate(BaseModel):
    """Schema for creating a newsletter."""
    title: str
    content: str

class NewsletterResponse(BaseModel):
    """Schema for newsletter response."""
    id: int
    title: str
    content: str
    created_at: datetime

class NewsletterUpdate(BaseModel):
    """Schema for updating a newsletter."""
    title: str
    content: str
