from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


DbSession = Depends(db_session)
