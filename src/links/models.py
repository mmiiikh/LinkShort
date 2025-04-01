from sqlalchemy import Table, Column, Integer, DateTime, MetaData, String
from datetime import datetime, timezone
metadata = MetaData()

links = Table(
    "links",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("original_url", String),
    Column("short_code", String, unique = True),
    Column("created_at", DateTime, nullable=False, default=datetime.now()),
    Column("last_accessed", DateTime),
    Column("accesses", Integer, default=0),
    Column("expires_at", DateTime)
)