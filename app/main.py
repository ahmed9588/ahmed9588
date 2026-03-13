from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Conversational Sector AI Platform",
    version="0.1.0",
    description="Blueprint-to-tool governed platform MVP",
)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


app.include_router(router)
