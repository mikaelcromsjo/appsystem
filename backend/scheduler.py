import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.models import Alarm
from core.models.models import User
from core.database import SessionLocal
from state import active_connections

logger = logging.getLogger(__name__)


async def alarm_scheduler():
    logger.info("✅ Alarm scheduler started.")
    while True:
        await asyncio.sleep(60)
        db: Session = SessionLocal()
        now = datetime.now(timezone.utc)
        logger.info(f"Scheduler running at {now.isoformat()} utc")
        try:
            due_alarms = (
                db.query(Alarm)
                .filter(Alarm.date >= now)
                .filter(
                    or_(
                        and_(
                            Alarm.reminder <= now,
                            Alarm.reminder_sent.is_(None)
                        ),
                        and_(
                            Alarm.date - timedelta(minutes=30) <= now,
                            Alarm.reminder_sent.isnot(None),
                            Alarm.reminder_sent < (Alarm.date - timedelta(minutes=30))
                        )
                    )
                )
                .all()
            )

            for alarm in due_alarms:
                users = db.query(User).filter(User.team_id == alarm.team_id).all()
                for user in users:
                    if not user:
                        continue
                    logger.info("✅ Send Alarm.")
                    payload = {
                        "type": "alarm",
                        "customer": f"{alarm.customer.first_name} {alarm.customer.last_name}",
                        "note": alarm.note,
                        "date": alarm.date.isoformat(),
                    }
                    for ws in active_connections.get(str(user.id), []):
                        try:
                            await ws.send_json(payload)
                            alarm.reminder_sent = now
                            db.commit()
                        except Exception as e:
                            logger.error(f"WebSocket send failed for {user.id}: {e}")

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            db.close()
