from fastapi import FastAPI
import routes
import logging
from models import NoMatchingFileError
from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

templates = routes.templates

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(routes.router)

@app.exception_handler(NoMatchingFileError)
async def link_not_found(request: Request, exc: NoMatchingFileError):
    return templates.TemplateResponse(
        request,
        "message.html",
        {
            "title": "This link doesn't work",
            "message": "Check you copied the whole link. If you did, the file has expired or been deleted.",
        },
        status_code=404,
    )