from datetime import datetime

from pydantic import BaseModel


class LinkCreate(BaseModel):
    original_url: str
    custom_alias: str = None
    expires_at: datetime = None


class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    accesses: int
    last_accessed: datetime = None


