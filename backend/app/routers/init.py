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
    default_user = crud.ensure_default_user(db)

    if not crud.get_villages_by_user_id(db, default_user.id):
        crud.create_village(db, models.VillageCreate(name="My New Village", user_id=default_user.id))

    return {"message": "Data initialized"}
