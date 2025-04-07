import os
import sys
from functools import lru_cache
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine


# prepare for PyInstaller
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:  # Normal dev environment
        return os.path.dirname(os.path.abspath(__file__))


@lru_cache
def get_data_dir():
    base_dir = get_base_dir()
    data_path = os.path.join(base_dir, "data")
    os.makedirs(data_path, exist_ok=True)
    return data_path


@lru_cache
def get_db_path():
    return f"sqlite:///{os.path.join(get_data_dir(), 'wordcloud.db')}"


@lru_cache
def get_sql_engine(engine_url: str | None = None, db_name: str = "wordcloud"):
    engine_url = get_db_path() if engine_url is None else engine_url
    engine = create_engine(engine_url, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
