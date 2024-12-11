"""Main FastAPI application entry point."""
from fastapi import FastAPI, Depends, Cookie, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database.config import Base, engine, get_db
from database.triggers import setup_model_trigger
from models.newsletter import Newsletter, NewsletterCreate, NewsletterResponse, NewsletterUpdate
from models.auth import UserLogin
from api.auth import login
from api.newsletters import (
    create_newsletter,
    get_newsletters,
    update_newsletter,
    newsletter_events
)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"]
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create database tables
Base.metadata.create_all(bind=engine)

# Setup database triggers on startup
@app.on_event("startup")
async def startup_event():
    await setup_model_trigger(Newsletter)

# Register routes
app.post("/auth")(login)
app.post("/newsletters", response_model=NewsletterResponse)(create_newsletter)
app.get("/newsletters", response_model=list[NewsletterResponse])(get_newsletters)
app.put("/newsletters/{newsletter_id}")(update_newsletter)
app.get("/newsletter/events")(newsletter_events)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
