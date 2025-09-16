from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from chat_bot.routes import router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
