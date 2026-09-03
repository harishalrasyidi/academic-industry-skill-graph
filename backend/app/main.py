from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .fuseki import FusekiError, execute_select, execute_sparql, sparql_iri
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


async def resource_details(uri: str):
    subject = sparql_iri(uri)
    rows = await execute_select(f"""
        SELECT ?predicate ?object ?objectType
        WHERE {{
            {subject} ?predicate ?object .
            BIND(IF(isIRI(?object), "iri", IF(isBlank(?object), "blank", "literal")) AS ?objectType)
        }}
        ORDER BY ?predicate
    """)
    return {"uri": uri, "properties": rows}


@app.get("/api/resources")
async def get_resource(uri: str):
    try:
        return await resource_details(uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FusekiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/properties")
async def get_property(uri: str):
    try:
        property_iri = sparql_iri(uri)
        rows = await execute_select(f"""
            SELECT ?type ?domain ?range
            WHERE {{
                {property_iri} a ?type .
                OPTIONAL {{ {property_iri} <http://www.w3.org/2000/01/rdf-schema#domain> ?domain }}
                OPTIONAL {{ {property_iri} <http://www.w3.org/2000/01/rdf-schema#range> ?range }}
            }}
        """)
        examples = await execute_select(f"""
            SELECT ?subject ?value
            WHERE {{ ?subject {property_iri} ?value }}
            LIMIT 30
        """)
        return {"uri": uri, "metadata": rows, "examples": examples}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FusekiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/term-info")
async def get_term_info(uri: str):
    try:
        term = sparql_iri(uri)
        rows = await execute_select(f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT ?type
            WHERE {{
                {term} a ?type .
                FILTER(?type IN (owl:ObjectProperty, owl:DatatypeProperty, owl:Class))
            }}
        """)
        types = {row["type"]["value"] for row in rows if row.get("type")}
        property_types = {
            "http://www.w3.org/2002/07/owl#ObjectProperty",
            "http://www.w3.org/2002/07/owl#DatatypeProperty",
        }
        kind = "property" if types & property_types else "entity"
        return {"uri": uri, "kind": kind, "types": sorted(types)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FusekiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc