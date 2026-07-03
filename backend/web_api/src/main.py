import uuid
from datetime import datetime, timezone

import nanoid
from fastapi import Depends, FastAPI, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from .config import IDEMPOTENCY_KEY_TTL_SECONDS, REDIS_URL
from .database import get_db
from .kafka_producer import publish_view_event
from .models import Category, Paste, VisitCount
from .schemas import CategoryOut, PasteCreate, PasteCreatedOut, PasteOut


app = FastAPI(title="My Awesome Pastebin API", version="1.0.0")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


@app.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.post("/pastes", response_model=PasteCreatedOut, status_code=201)
def create_paste(body: PasteCreate, db: Session = Depends(get_db)):
    category = db.get(Category, body.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    paste = Paste(
        uid=nanoid.generate(),
        title=body.title,
        category_id=body.category_id,
        syntax=body.syntax,
        raw_data=body.raw_data,
        expiration_datetime=body.expiration_datetime,
        password=body.password,
        burn_after_read=body.burn_after_read,
        created_at=datetime.now(timezone.utc),
    )
    db.add(paste)

    visit_count = VisitCount(paste=paste, count=0, last_updated=datetime.now(timezone.utc))
    db.add(visit_count)

    db.commit()
    return paste


@app.get("/pastes/{uid}", response_model=PasteOut)
def get_paste(uid: str, password: str | None = Query(default=None), db: Session = Depends(get_db)):
    paste = db.query(Paste).filter(Paste.uid == uid, Paste.deleted.is_(False)).first()
    if not paste:
        raise HTTPException(status_code=404, detail="Paste not found")

    if paste.expiration_datetime and paste.expiration_datetime <= datetime.now(timezone.utc):
        paste.deleted = True
        db.commit()
        raise HTTPException(status_code=404, detail="Paste has expired")

    if paste.password and paste.password != password:
        raise HTTPException(status_code=403, detail="Invalid password")

    idempotency_key = str(uuid.uuid4())
    redis_key = f"idem:{idempotency_key}"
    if redis_client.set(redis_key, "1", ex=IDEMPOTENCY_KEY_TTL_SECONDS, nx=True):
        publish_view_event(paste.uid, idempotency_key)

    if paste.burn_after_read:
        paste.deleted = True
        db.commit()

    return paste
