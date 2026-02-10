from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

from app.core.config import settings



engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG, 
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session