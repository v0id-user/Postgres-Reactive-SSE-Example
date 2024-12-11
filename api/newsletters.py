"""Newsletter-related endpoints and event streaming."""
import json
import asyncio
from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from database.config import get_db, get_db_connection
from models.newsletter import Newsletter, NewsletterCreate, NewsletterResponse, NewsletterUpdate
from api.auth import get_current_user

async def create_newsletter(
    newsletter: NewsletterCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
) -> NewsletterResponse:
    """Create a new newsletter."""
    db_newsletter = Newsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter

async def get_newsletters(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
) -> List[NewsletterResponse]:
    """Get all newsletters, ordered by creation date."""
    newsletters = db.query(Newsletter).order_by(Newsletter.created_at.desc()).all()
    return newsletters

async def update_newsletter(
    newsletter_id: int,
    newsletter: NewsletterUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update an existing newsletter."""
    db_newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    
    if not db_newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    db_newsletter.title = newsletter.title
    db_newsletter.content = newsletter.content
    db.commit()
    
    return {"message": "Newsletter updated successfully"}

async def newsletter_events(current_user: str = Depends(get_current_user)):
    """Stream newsletter events using Server-Sent Events."""
    async def event_generator():
        conn = None
        try:
            conn = await get_db_connection()
            queue = asyncio.Queue()
            
            def handle_notification(connection, pid, channel, payload):
                try:
                    if isinstance(payload, str):
                        parsed = json.loads(payload)
                        asyncio.create_task(queue.put(json.dumps(parsed)))
                    else:
                        asyncio.create_task(queue.put(json.dumps(payload)))
                except Exception as e:
                    print(f"Error processing notification: {e}")
            
            await conn.add_listener('newsletters_changes', handle_notification)
            
            # Send initial retry time
            yield {
                "retry": 5000,
                "data": ""
            }
            
            while True:
                try:
                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=30)
                        yield {
                            "event": "newsletter",
                            "data": payload
                        }
                    except asyncio.TimeoutError:
                        yield {
                            "event": "ping",
                            "data": "ping"
                        }
                except Exception as e:
                    print(f"Error in event loop: {e}")
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
        ping=30,
    )

__all__ = ['create_newsletter', 'get_newsletters', 'update_newsletter', 'newsletter_events']
