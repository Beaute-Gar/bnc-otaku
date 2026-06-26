from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from backend.config import settings

engine = create_engine(
    settings.database_url,
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


def init_db():
    Base.metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            # Migrations
            conn.execute(
                text("ALTER TABLE quiz_questions MODIFY difficulty VARCHAR(30) NOT NULL")
            )
            conn.execute(
                text("ALTER TABLE exam_sessions MODIFY level VARCHAR(30) DEFAULT NULL")
            )
            conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS highest_unlocked VARCHAR(30) DEFAULT 'Junior Otaku'")
            )
            conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS completed_levels TEXT DEFAULT '[]'")
            )
            conn.commit()
    except Exception:
        pass
