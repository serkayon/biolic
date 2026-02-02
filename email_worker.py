# email_worker.py
import threading
import queue
import logging
from email_service import email_service

logger = logging.getLogger(__name__)

email_queue = queue.Queue()

def email_worker():
    while True:
        email, otp = email_queue.get()
        try:
            email_service.send_otp_email(email, otp)
            logger.info(f"Email sent to {email}")
        except Exception as e:
            logger.error(f"Email failed for {email}: {e}")
        finally:
            email_queue.task_done()

threading.Thread(target=email_worker, daemon=True).start()
