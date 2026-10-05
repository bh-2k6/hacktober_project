from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import HOST, PORT, UPLOAD_DIR
from app.database import init_db
from app.routes import items, matches, dashboard

app = FastAPI(
    title="AI Lost & Found",
    description="AI-powered lost and found matching for college campuses",
    version="1.0.0",
)

init_db()

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "app" / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(items.router)
app.include_router(matches.router)
app.include_router(dashboard.router)


@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent / "app" / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-lost-and-found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
