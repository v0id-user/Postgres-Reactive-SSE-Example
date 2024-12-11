"""Authentication models."""
from pydantic import BaseModel

class UserLogin(BaseModel):
    """Schema for user login credentials."""
    username: str
    password: str
