from fastapi import FastAPI
import routes
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(routes.router)