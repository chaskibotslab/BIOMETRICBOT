"""
Conexión a Base de Datos PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from config import settings
from models import Base

# Crear engine
engine = create_engine(
    settings.db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # Cambiar a True para ver SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Crea las tablas si no existen"""
    Base.metadata.create_all(bind=engine)
    migrate_db()
    print("✅ Base de datos inicializada")


def migrate_db():
    """Agrega columnas nuevas a tablas existentes (safe migration)"""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE sucursales ADD COLUMN IF NOT EXISTS hora_entrada TIME",
        "ALTER TABLE sucursales ADD COLUMN IF NOT EXISTS hora_salida TIME",
        "ALTER TABLE sucursales ADD COLUMN IF NOT EXISTS tolerancia_minutos INTEGER DEFAULT 15",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception as e:
                print(f"[MIGRATION] Skip: {e}")
        conn.commit()

    # Reset admin password (TEMPORAL - eliminar despues de usar)
    try:
        from services.auth_service import hash_password
        new_hash = hash_password("Admin2026!")
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE usuarios_sistema SET password_hash = :h WHERE username = 'admin'"
            ), {"h": new_hash})
            conn.commit()
        print("✅ Password admin reseteada a: Admin2026!")
    except Exception as e:
        print(f"[MIGRATION] Password reset skip: {e}")

    print("✅ Migraciones aplicadas")


def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager para usar fuera de FastAPI"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
