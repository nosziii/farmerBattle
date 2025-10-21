import asyncio
import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from .routers import village, buildings, leaderboard, map, battle, user, init, troops, admin, expeditions, auth as auth_router
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
app.include_router(expeditions.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(auth_router.router, prefix="")
app.include_router(websocket.router)



async def process_training_queue_task():
    db = SessionLocal()
    try:
        while True:
            completed_villages = crud.process_training_queue(db)
            for village_id in completed_villages:
                await websocket.manager.broadcast(f"village:{village_id}:training_finished")
            await asyncio.sleep(1)
    finally:
        db.close()

async def process_resource_generation_task():
    db = SessionLocal()
    try:
        while True:
            updates = crud.process_resource_generation(db)
            for update in updates:
                payload = {
                    "type": "resources_updated",
                    "village_id": update["village_id"],
                    "resources": update["resources"],
                    "capacities": update["capacities"],
                }
                await websocket.manager.broadcast(json.dumps(payload))
            await asyncio.sleep(crud.RESOURCE_TICK_SECONDS)
    finally:
        db.close()

async def process_building_queue_task():
    db = SessionLocal()
    try:
        while True:
            updates = crud.process_building_queue(db)
            for update in updates:
                payload = json.dumps(
                    {
                        "type": "building_upgrade_finished",
                        "village_id": update["village_id"],
                        "building": update["building"],
                        "level": update["level"],
                    }
                )
                await websocket.manager.broadcast(payload)
            await asyncio.sleep(1)
    finally:
        db.close()

async def process_barbarian_growth_task():
    db = SessionLocal()
    try:
        while True:
            updates = crud.process_barbarian_growth(db)
            if updates:
                payload = json.dumps(
                    {
                        "type": "barbarian_village_updated",
                        "updates": updates,
                    }
                )
                await websocket.manager.broadcast(payload)
            await asyncio.sleep(crud.BARBARIAN_GROWTH_TICK_SECONDS)
    finally:
        db.close()


async def process_expedition_task():
    db = SessionLocal()
    try:
        while True:
            updated_villages, expedition_summaries = crud.process_expeditions(db)
            for village_id in updated_villages:
                await websocket.manager.broadcast(f"village:{village_id}:expedition_updated")
            for summary in expedition_summaries:
                payload = json.dumps(
                    {
                        "type": "expedition_update",
                        "village_id": summary.village_id,
                        "expedition": summary.model_dump(),
                    }
                )
                await websocket.manager.broadcast(payload)
            await asyncio.sleep(5)
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        crud.ensure_default_user(db)
        crud.create_initial_troops(db)
    finally:
        db.close()
    asyncio.create_task(process_training_queue_task())
    asyncio.create_task(process_resource_generation_task())
    asyncio.create_task(process_building_queue_task())
    asyncio.create_task(process_barbarian_growth_task())
    asyncio.create_task(process_expedition_task())

@app.get("/")
def read_root():
    return {"message": "Welcome to Farmer Battle API"}
