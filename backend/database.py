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
    # Migration : passer difficulty de ENUM à VARCHAR(30)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE quiz_questions MODIFY difficulty VARCHAR(30) NOT NULL")
            )
            conn.execute(
                text("ALTER TABLE exam_sessions MODIFY level VARCHAR(30) DEFAULT NULL")
            )
            conn.commit()
    except Exception:
        pass  # Déjà migré ou table n'existe pas encore
