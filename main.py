from fastapi import FastAPI, Depends, Cookie, Response, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, declarative_base, scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import select
import asyncpg
import asyncio
import json
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Only allow our own origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"]  # Explicitly expose Set-Cookie header
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
POSTGRESQL_LOCAL = "postgresql://root:root@localhost:5432/dum_db"
engine = create_engine(POSTGRESQL_LOCAL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create PostgreSQL trigger function and trigger
async def setup_model_trigger(model_class):
    """
    Create a PostgreSQL trigger for any SQLAlchemy model class.
    The trigger will notify on INSERT operations with all columns from the model.
    
    Args:
        model_class: SQLAlchemy model class that inherits from Base
    """
    if not hasattr(model_class, '__table__'):
        raise ValueError("Input must be a SQLAlchemy model class")

    table_name = model_class.__tablename__
    channel_name = f"{table_name}_changes"
    trigger_name = f"{table_name}_notify_trigger"
    function_name = f"notify_{table_name}_change"
    
    # Get all column names from the model
    columns = [column.name for column in model_class.__table__.columns]
    
    # Build the JSON object dynamically based on columns
    json_fields = ',\n                        '.join([f"'{col}', NEW.{col}" for col in columns])
    
    conn = await asyncpg.connect(POSTGRESQL_LOCAL)
    try:
        # Create the trigger function
        await conn.execute(f"""
            CREATE OR REPLACE FUNCTION {function_name}()
            RETURNS trigger AS $$
            BEGIN
                PERFORM pg_notify(
                    '{channel_name}',
                    json_build_object(
                        'operation', TG_OP,
                        {json_fields}
                    )::text
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create the trigger if it doesn't exist
        await conn.execute(f"""
            DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};
            CREATE TRIGGER {trigger_name}
                AFTER INSERT OR UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION {function_name}();
        """)
    finally:
        await conn.close()

# Models
class Newsletter(Base):
    __tablename__ = "newsletters"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables and setup trigger
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    await setup_model_trigger(Newsletter)

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class NewsletterCreate(BaseModel):
    title: str
    content: str

class NewsletterResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

class NewsletterUpdate(BaseModel):
    title: str
    content: str

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_connection():
    return await asyncpg.connect(POSTGRESQL_LOCAL)

async def get_current_user(session: Optional[str] = Cookie(None)):
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session

# Auth endpoint
@app.post("/auth")
async def login(user_data: UserLogin):
    response = Response(
        content=json.dumps({"message": "Logged in successfully"}),
        media_type="application/json"
    )
    response.set_cookie(
        key="session",
        value=user_data.username,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/"
    )
    return response

# Newsletter endpoints
@app.post("/newsletters", response_model=NewsletterResponse)
async def create_newsletter(
    newsletter: NewsletterCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_newsletter = Newsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter  # The trigger will handle the notification

@app.get("/newsletters", response_model=List[NewsletterResponse])
async def get_newsletters(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    newsletters = db.query(Newsletter).order_by(Newsletter.created_at.desc()).all()
    return newsletters

@app.put("/newsletters/{newsletter_id}")
async def update_newsletter(newsletter_id: int, newsletter: NewsletterUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    
    if not db_newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    db_newsletter.title = newsletter.title
    db_newsletter.content = newsletter.content
    db.commit()
    
    return {"message": "Newsletter updated successfully"}

@app.get("/newsletter/events")
async def events(current_user: str = Depends(get_current_user)):
    async def event_generator():
        conn = None
        try:
            conn = await get_db_connection()
            queue = asyncio.Queue()
            
            def handle_notification(connection, pid, channel, payload):
                print(f"Received notification: {payload} - {channel} - {pid} - {connection}")
                try:
                    # If payload is a string, parse it to ensure it's valid JSON
                    if isinstance(payload, str):
                        parsed = json.loads(payload)
                        asyncio.create_task(queue.put(json.dumps(parsed)))
                    else:
                        asyncio.create_task(queue.put(json.dumps(payload)))
                except Exception as e:
                    print(f"Error processing notification: {e}")
            
            await conn.add_listener('newsletters_changes', handle_notification)
            print("Added listener for newsletters_changes")
            
            # Send initial retry time
            yield {
                "retry": 5000,  # Client retry timeout in milliseconds
                "data": ""  # Empty data for retry message
            }
            
            # Keep connection alive with periodic pings
            while True:
                try:
                    # Try to get a notification with a timeout
                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=30)
                        yield {
                            "event": "newsletter",
                            "data": payload
                        }
                    except asyncio.TimeoutError:
                        # Send a ping every 30 seconds to keep connection alive
                        yield {
                            "event": "ping",
                            "data": "ping"
                        }
                        
                except Exception as e:
                    print(f"Error in event loop: {e}")
                    # Don't break the loop on error, just continue
                    continue
                    
        except Exception as e:
            print(f"Error in event generator: {e}")
            if conn:
                await conn.close()
            raise
            
        finally:
            if conn:
                await conn.close()
    
    return EventSourceResponse(
        event_generator(),
        ping=30,  # Send ping every 30 seconds
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
