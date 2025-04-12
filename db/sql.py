import sqlite3
import datetime
import threading
from typing import List, Dict

from core import BASE_DIR
from core.log_config import db_logger as logger

DB_NAME = BASE_DIR / "tickets.db"
_get_tickets_lock = threading.Lock()


def init_db():
    """Initialize database schema"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                last_processed_at TIMESTAMP NULL
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tickets(status)")
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def add_tickets(ticket_ids: List[int]) -> int:
    """
    Insert new tickets into database.
    If duplicate ticket_id exists, delete and reinsert it.
    Returns count of (re)inserted tickets.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            inserted = 0
            for ticket_id in ticket_ids:
                # Delete if already exists
                cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
                cursor.execute(
                    "INSERT INTO tickets (ticket_id, status) VALUES (?, 'pending')",
                    (ticket_id,)
                )
                inserted += 1
            conn.commit()
            logger.info(f"Successfully added {inserted} tickets: {ticket_ids}")
            return inserted
    except Exception as e:
        logger.error(f"Failed to add tickets {ticket_ids}: {str(e)}")
        raise


def get_tickets_for_processing(limit: int = 100) -> List[Dict]:
    """
    Get tickets that are either:
    - Pending (never processed), OR
    - Stuck in processing for >15 minutes
    Marks them immediately as 'processing'.
    Thread-safe using a lock.
    """
    with _get_tickets_lock:
        try:
            fifteen_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=15)
            with sqlite3.connect(DB_NAME) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticket_id 
                    FROM tickets 
                    WHERE status = 'pending' 
                    OR (status = 'processing' AND last_processed_at < ?)
                    ORDER BY created_at
                    LIMIT ?
                    """, (fifteen_min_ago.isoformat(), limit))

                rows = cursor.fetchall()
                ticket_ids = [row["ticket_id"] for row in rows]

                if not ticket_ids:
                    logger.info("No tickets found for processing")
                    return []

                # Mark as processing
                now = datetime.datetime.now().isoformat()
                cursor.executemany("""
                    UPDATE tickets 
                    SET status = 'processing', last_processed_at = ? 
                    WHERE ticket_id = ?
                """, [(now, tid) for tid in ticket_ids])

                conn.commit()
                logger.info(f"Retrieved and marked {len(ticket_ids)} tickets for processing: {ticket_ids}")
                return [{"ticket_id": tid, "status": "processing"} for tid in ticket_ids]
        except Exception as e:
            logger.error(f"Failed to get tickets for processing: {str(e)}")
            raise


def mark_as_processing(ticket_id: str) -> bool:
    """Mark ticket as being processed"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tickets 
                SET status = 'processing', 
                    last_processed_at = CURRENT_TIMESTAMP 
                WHERE ticket_id = ?
                """, (ticket_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Successfully marked ticket {ticket_id} as processing")
            else:
                logger.warning(f"Failed to mark ticket {ticket_id} as processing - ticket not found")
            return success
    except Exception as e:
        logger.error(f"Failed to mark ticket {ticket_id} as processing: {str(e)}")
        raise


def delete_tickets(ticket_ids: List[str]) -> int:
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "DELETE FROM tickets WHERE ticket_id = ? AND status = 'processing'",
                [(ticket_id,) for ticket_id in ticket_ids]
            )
            conn.commit()
            deleted_count = cursor.rowcount
            return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete tickets {ticket_ids}: {str(e)}")
        raise
