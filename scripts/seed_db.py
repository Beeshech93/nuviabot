#!/usr/bin/env python3
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import Base, engine, SessionLocal
from app.db.seed import seed_database

def main():
    print("Creating all tables in database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        print("Database initialized successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()

