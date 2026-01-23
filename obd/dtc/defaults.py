from typing import Optional
from .database import DTCDatabase

_default_db: Optional[DTCDatabase] = None


def get_database(manufacturer: Optional[str] = None) -> DTCDatabase:
    global _default_db
    if _default_db is None or manufacturer:
        _default_db = DTCDatabase(manufacturer=manufacturer)
    return _default_db


def lookup_code(code: str) -> str:
    db = get_database()
    return db.get_description(code)
