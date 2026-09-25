from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

URL = "sqlite:///./ecommerce.db"

engine = create_engine(
    URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()