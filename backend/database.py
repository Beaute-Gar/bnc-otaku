from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from backend.config import settings

engine = create_engine(
    settings.resolved_database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
)

session_factory = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


import backend.models.admin  # noqa
import backend.models.quiz  # noqa


def init_db():
    Base.metadata.create_all(engine)
    if settings.is_postgres:
        _run_pg_migrations()
    else:
        _run_mysql_migrations()


def _run_mysql_migrations():
    migrations = [
        "ALTER TABLE quiz_questions MODIFY difficulty VARCHAR(30) NOT NULL",
        "ALTER TABLE exam_sessions MODIFY level VARCHAR(30) DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN highest_unlocked VARCHAR(30) DEFAULT 'Junior Otaku'",
        "ALTER TABLE users ADD COLUMN completed_levels VARCHAR(255) DEFAULT '[]'",
    ]
    for sql in migrations:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception:
            pass


def _run_pg_migrations():
    migrations = [
        "ALTER TABLE quiz_questions ALTER COLUMN difficulty TYPE VARCHAR(30)",
        "ALTER TABLE quiz_questions ALTER COLUMN difficulty SET NOT NULL",
        "ALTER TABLE exam_sessions ALTER COLUMN level TYPE VARCHAR(30)",
        "ALTER TABLE exam_sessions ALTER COLUMN level DROP NOT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS highest_unlocked VARCHAR(30) DEFAULT 'Junior Otaku'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS completed_levels VARCHAR(255) DEFAULT '[]'",
    ]
    for sql in migrations:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception:
            pass
