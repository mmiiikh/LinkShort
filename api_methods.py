from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import string
import random
from api_config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)


class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    accesses = Column(Integer, default=0)
    expires_at = Column(DateTime)


Base.metadata.create_all(bind=engine)


class LinkCreate(BaseModel):
    original_url: str
    custom_alias: str = None
    expires_at: datetime = None


class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    accesses: int
    last_accessed: datetime = None


@app.post("/links/shorten")
def shorten_link(link: LinkCreate):
    db = SessionLocal()

    if link.custom_alias:
        short_code = link.custom_alias
    else:
        short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    if db.query(Link).filter(Link.short_code == short_code).first():
        db.close()
        raise HTTPException(status_code=400, detail="Custom alias already exists")

    new_link = Link(
        original_url=link.original_url,
        short_code=short_code,
        expires_at=link.expires_at
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    db.close()

    return {"shortened_url": f"https://shorturl.at/{short_code}"}


@app.get("/{short_code}")
def redirect_link(short_code: str):
    db = SessionLocal()
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if link: #and (link.expires_at is None or link.expires_at > datetime.now(timezone.utc)):
        link.accesses += 1
        link.last_accessed = datetime.now(timezone.utc)
        db.commit()
        db.close()

        return {"redirect_url": link.original_url}

    db.close()
    raise HTTPException(status_code=404, detail="Link not found or expired")


@app.get("/links/{short_code}/stats", response_model=LinkStats)
def link_stats(short_code: str):
    db = SessionLocal()
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if link:
        db.close()
        return {
            "original_url": link.original_url,
            "created_at": link.created_at,
            "accesses": link.accesses,
            "last_accessed": link.last_accessed
        }

    db.close()
    raise HTTPException(status_code=404, detail="Link not found")


@app.delete("/links/{short_code}")
def delete_link(short_code: str):
    db = SessionLocal()
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if link:
        db.delete(link)
        db.commit()
        db.close()
        return {"message": "Link deleted"}

    db.close()
    raise HTTPException(status_code=404, detail="Link not found")


@app.put("/links/{short_code}")
def update_link(short_code: str, new_url: str):
    db = SessionLocal()
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if link:
        link.original_url = new_url
        db.commit()
        db.close()
        return {"message": "Link updated"}

    db.close()
    raise HTTPException(status_code=404, detail="Link not found")


@app.get("/links/search")
def search_link(original_url: str):
    db = SessionLocal()
    link = db.query(Link).filter(Link.original_url == original_url).first()

    if link:
        db.close()
        return {"shortened_url": f"http://localhost:8000/{link.short_code}"}

    db.close()
    raise HTTPException(status_code=404, detail="Link not found")


@app.delete("/clean_up")
def clean_up_links():
    db = SessionLocal()
    expired_links = db.query(Link).filter(Link.expires_at < datetime.utcnow()).all()

    for link in expired_links:
        db.delete(link)

    db.commit()
    db.close()
    return {"message": "Expired links removed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_methods:app", reload = True)

#host="0.0.0.0", port=8000,