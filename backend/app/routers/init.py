from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/init/")
def init_data(db: Session = Depends(get_db)):
    crud.create_initial_troops(db)
    try:
        crud.create_user(db, models.UserCreate(username="testuser", password="password"))
    except:
        db.rollback() # User already exists

    if not crud.get_villages_by_user_id(db, 1):
        crud.create_village(db, models.VillageCreate(name="My New Village"))

    return {"message": "Data initialized"}
