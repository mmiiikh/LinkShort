from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
import time
from src.database import get_async_session
from .models import links
from .schemas import LinkCreate, LinkStats
from fastapi_cache.decorator import cache
import random
import string
from datetime import datetime, timezone


router = APIRouter(
    prefix="/links",
    tags=["links"]
)


@router.get("/long")
@cache(expire=60)
async def get_long():
    time.sleep(5)
    return "hello"


@router.post("/links/shorten")
async def shorten_link(link: LinkCreate, session: AsyncSession = Depends(get_async_session)):
    if link.custom_alias:
        short_code = link.custom_alias
    else:
        short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    query = await session.execute(select(links).filter(links.c.short_code == short_code))
    existing_link = query.scalars().first()

    if existing_link:
        raise HTTPException(status_code=400, detail="Custom alias already exists")

    new_link_data = {
        "original_url": link.original_url,
        "short_code": short_code,
        "expires_at": link.expires_at,
        "created_at": datetime.now(),
        "last_accessed": None,
        "accesses": 0
    }

    await session.execute(links.insert().values(new_link_data))
    await session.commit()

    return {"shortened_url": f"https://shorturl.at/{short_code}"}

@router.get("/{short_code}")
async def redirect_link(short_code: str, session: AsyncSession = Depends(get_async_session)):
    query = await session.execute(select(links).filter(links.c.short_code == short_code))
    link = query.fetchone()

    if link:
    #    link.accesses += 1
    #    link.last_accessed = datetime.now(timezone.utc)
    #    await session.commit()

        return {"redirect_url": link.original_url}

    raise HTTPException(status_code=404, detail="Link not found or expired")