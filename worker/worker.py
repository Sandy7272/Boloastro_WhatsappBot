import queue
import threading
import logging

from backend.engines.ai_engine import ask_ai
from backend.engines.pdf_engine import generate_pdf
from backend.engines.astro_engine import get_kundali_cached

logger = logging.getLogger(__name__)

# =========================
# TASK QUEUE
# =========================

TASK_QUEUE = queue.Queue()


# =========================
# WORKER LOOP
# =========================

def worker_loop():
    logger.info("⚙️ Background worker started")

    while True:
        task = TASK_QUEUE.get()

        try:
            task_type = task["type"]

            if task_type == "AI":
                ask_ai(
                    task["phone"],
                    task["question"],
                    task["data"]
                )

            elif task_type == "PDF":
                generate_pdf(
                    task["phone"],
                    task["data"]
                )

            elif task_type == "KUNDALI":
                get_kundali_cached(
                    task["data"]
                )

        except Exception:
            logger.exception("❌ Worker task failed")

        finally:
            TASK_QUEUE.task_done()


# =========================
# START WORKER THREAD
# =========================

def start_worker():
    thread = threading.Thread(
        target=worker_loop,
        daemon=True
    )
    thread.start()


# =========================
# ENQUEUE HELPERS
# =========================

def enqueue_ai(phone, question, data):
    TASK_QUEUE.put({
        "type": "AI",
        "phone": phone,
        "question": question,
        "data": data
    })


def enqueue_pdf(phone, data):
    TASK_QUEUE.put({
        "type": "PDF",
        "phone": phone,
        "data": data
    })


def enqueue_kundali(data):
    TASK_QUEUE.put({
        "type": "KUNDALI",
        "data": data
    })
