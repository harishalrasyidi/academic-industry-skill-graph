from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .fuseki import FusekiError, execute_sparql
from .schemas import SparqlQueryRequest

app = FastAPI(title="LOD Explorer SPARQL API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"service": "LOD Explorer", "status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query")
async def query_sparql(request: SparqlQueryRequest):
    try:
        return await execute_sparql(request.query)
    except FusekiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc