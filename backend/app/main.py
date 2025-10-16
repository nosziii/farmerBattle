import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from .routers import village, buildings, leaderboard, map, battle, user, init, troops
from . import websocket
from . import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(village.router, prefix="/api")
app.include_router(buildings.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(map.router, prefix="/api")
app.include_router(battle.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(init.router, prefix="/api")
app.include_router(troops.router, prefix="/api")
app.include_router(websocket.router)

async def process_training_queue_task():
    db = SessionLocal()
    while True:
        crud.process_training_queue(db)
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_training_queue_task())

@app.get("/")
def read_root():
    return {"message": "Welcome to Farmer Battle API"}
