#!/usr/bin/env python3
"""
NUVIO GROWTH BOT - SUPABASE POSTGRESQL INITIALIZER
Creates tables and seeds initial data into your live Supabase project.

Usage:
    python scripts/setup_supabase.py [DATABASE_PASSWORD_OR_FULL_URL]
"""
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.db.seed import seed_database
from app.config import settings

def main():
    target_url = None

    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.startswith("postgresql://") or arg.startswith("postgres://"):
            target_url = arg
        else:
            # Assume it's the database password for user 'postgres'
            project_id = "zghqluchsptyvuyhbyjm"
            target_url = f"postgresql://postgres:{arg}@db.{project_id}.supabase.co:5432/postgres?sslmode=require"
    elif os.getenv("DATABASE_URL") and not os.getenv("DATABASE_URL").startswith("sqlite"):
        target_url = os.getenv("DATABASE_URL")
    else:
        print("=" * 65)
        print("  NUVIO GROWTH BOT - SUPABASE POSTGRESQL SETUP")
        print("=" * 65)
        print("Para conectar y crear las tablas en Supabase:")
        print("1. Ejecuta:")
        print("   python scripts/setup_supabase.py <TU_CONTRASEÑA_DE_SUPABASE>")
        print("   o")
        print("   python scripts/setup_supabase.py 'postgresql://postgres:PASSWORD@db.zghqluchsptyvuyhbyjm.supabase.co:5432/postgres?sslmode=require'")
        print("=" * 65)
        return

    # Normalize dialect
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"🔗 Conectando a Supabase PostgreSQL...")
    engine = create_engine(target_url, pool_pre_ping=True)

    try:
        print("📦 Creando todas las tablas del esquema en Supabase...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas con éxito.")

        SessionSupabase = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionSupabase()
        try:
            print("🌱 Sembrando planes, organización principal y usuarios en Supabase...")
            seed_database(db)
            print("🎉 ¡Base de datos de Supabase inicializada y lista para producción!")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Error al inicializar Supabase: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

