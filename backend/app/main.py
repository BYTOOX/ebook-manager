from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine

app = FastAPI(title="ebook-manager API")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/ebooks", response_model=list[schemas.EbookRead])
def list_ebooks(db: Session = Depends(get_db)):
    return db.query(models.Ebook).order_by(models.Ebook.id.desc()).all()


@app.post("/ebooks", response_model=schemas.EbookRead)
def create_ebook(payload: schemas.EbookCreate, db: Session = Depends(get_db)):
    ebook = models.Ebook(**payload.model_dump())
    db.add(ebook)
    db.commit()
    db.refresh(ebook)
    return ebook
