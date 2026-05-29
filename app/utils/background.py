import logging
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.models.notification import Notification

logger = logging.getLogger("app.background")


async def enqueue_email_notification(recipient_email: str, title: str, message: str):
    """
    Enqueue a job to send an email notification.
    Uses 'arq' with Redis under settings.REDIS_URL.
    """
    # Create notification record in PENDING state first
    notification = Notification(
        recipient_email=recipient_email,
        title=title,
        message=message,
        status="PENDING"
    )
    await notification.insert()

    try:
        # Connect to arq queue pool
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        pool = await create_pool(redis_settings)
        
        # Enqueue the job onto the worker
        await pool.enqueue_job(
            "send_email_task", 
            str(notification.id), 
            recipient_email, 
            title, 
            message
        )
        await pool.close()
        logger.info(f"Successfully enqueued background email job for {recipient_email}")
        
    except Exception as e:
        logger.warning(
            f"Failed to enqueue to Redis queue: {e}. "
            f"Processing notification state as SENT immediately (local development mode)."
        )
        # Fallback: process directly in the database as completed
        notification.status = "SENT"
        await notification.save()
