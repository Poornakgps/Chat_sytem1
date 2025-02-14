from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from db.database import create_tables
from routers import buyer, seller
from services.websocket import setup_websocket_routes

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    create_tables()

app.include_router(buyer.router)
app.include_router(seller.router)

setup_websocket_routes(app)
