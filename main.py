from fastapi import FastAPI
from routers import confluence_router

app = FastAPI()

app.include_router(confluence_router.router)
