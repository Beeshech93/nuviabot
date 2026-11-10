#!/usr/bin/env python3
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.services.publisher_service import PublisherService


async def scheduler_loop():
    print("🚀 NUVIO GROWTH BOT Publishing Scheduler running...")
    while True:
        db = SessionLocal()
        try:
            processed = await PublisherService.process_scheduled_queue(db)
            if processed > 0:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Processed and dispatched {processed} scheduled post(s).")
        except Exception as e:
            print(f"Error in scheduler tick: {e}")
        finally:
            db.close()

        # Check queue every 15 seconds
        await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        asyncio.run(scheduler_loop())
    except KeyboardInterrupt:
        print("Scheduler stopped.")

