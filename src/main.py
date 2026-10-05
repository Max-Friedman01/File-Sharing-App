from fastapi import FastAPI
import routes
import logging
from models import NoMatchingFileError
from fastapi import Request
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from cleanup import run_cleanup
import config

templates = routes.templates

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

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

async def cleanup_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(run_cleanup)
        except Exception:
            logger.exception("Cleanup failed")
        await asyncio.sleep(config.CLEANUP_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
