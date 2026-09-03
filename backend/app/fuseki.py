import httpx

from .config import FUSEKI_QUERY_URL, FUSEKI_TIMEOUT_SECONDS


class FusekiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


async def execute_sparql(query: str) -> dict:
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