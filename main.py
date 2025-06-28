from fastapi import FastAPI
from routes import router

app = FastAPI(title="Inventory API with Auth")

app.include_router(router)
