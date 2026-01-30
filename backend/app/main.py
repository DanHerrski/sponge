from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.graph import router as graph_router
from app.routes.nugget import router as nugget_router
from app.routes.upload import router as upload_router

app = FastAPI(title="Sponge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(nugget_router)
app.include_router(upload_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
