import logging
from arq.connections import RedisSettings
from app.core.config import settings
from app.db.mongo import init_db
from app.models.notification import Notification

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] arq.worker: %(message)s",
)
logger = logging.getLogger("arq.worker")


async def send_email_task(ctx, notification_id: str, recipient_email: str, title: str, message: str):
    """
    Background arq task simulating SMTP email delivery and updating database states.
    """
    logger.info(f"Processing background email to: {recipient_email} | Title: {title}")
    
    try:
        # SMTP email sending simulation
        # In a real production stack, we would integrate an SMTP server or SendGrid/Mailgun client here.
        logger.info(f"Simulating SMTP payload delivery to {recipient_email}...")
        
        # Retrieve the notification record to update status
        notification = await Notification.get(notification_id)
        if notification:
            notification.status = "SENT"
            await notification.save()
            logger.info(f"Notification document {notification_id} set to SENT.")
        else:
            logger.warning(f"Notification record with ID {notification_id} was not found.")
            
    except Exception as e:
        logger.error(f"Error delivering email for notification {notification_id}: {e}")
        notification = await Notification.get(notification_id)
        if notification:
            notification.status = "FAILED"
            await notification.save()


async def startup(ctx):
    """
    Runs when the background worker process spins up.
    Initializes Beanie ODM so database operations run safely in the background process.
    """
    logger.info("Initializing background worker Beanie connections...")
    await init_db()
    logger.info("Worker Beanie database context successfully established.")


async def shutdown(ctx):
    """
    Runs when the background worker shuts down.
    """
    logger.info("Worker connection pool shutting down.")


class WorkerSettings:
    """
    arq Worker Configuration Settings.
    To run: `arq app.worker.WorkerSettings`
    """
    functions = [send_email_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
