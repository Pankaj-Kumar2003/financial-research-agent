import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to SQLite for local development if DATABASE_URL is not set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_research.db")

# SQLite requires special check_same_thread argument
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency helper for database session acquisition."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

