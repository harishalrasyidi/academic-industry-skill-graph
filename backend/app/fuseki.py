import httpx
from urllib.parse import quote

from .config import FUSEKI_QUERY_URL, FUSEKI_TIMEOUT_SECONDS


class FusekiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


async def execute_sparql(query: str) -> dict:
    if not FUSEKI_QUERY_URL:
        raise FusekiError("FUSEKI_QUERY_URL belum dikonfigurasi.")
    try:
        async with httpx.AsyncClient(timeout=FUSEKI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                FUSEKI_QUERY_URL,
                content=query,
                headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
            )
    except httpx.RequestError as exc:
        raise FusekiError(f"Fuseki tidak dapat dihubungi: {exc}") from exc

    if response.is_error:
        detail = response.text.strip() or "Fuseki menolak query."
        raise FusekiError(detail, response.status_code)

    try:
        return response.json()
    except ValueError as exc:
        raise FusekiError("Fuseki mengirim respons yang bukan JSON SPARQL.", response.status_code) from exc


async def execute_select(query: str) -> list[dict]:
    result = await execute_sparql(query)
    return result.get("results", {}).get("bindings", [])


def sparql_iri(value: str) -> str:
    if not value.startswith(("http://", "https://")) or any(character in value for character in "<>\"{}|^`"):
        raise ValueError("URI RDF tidak valid.")
    return f"<{quote(value, safe=':/#?=&_%.-')}>"