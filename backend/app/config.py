import os


FUSEKI_QUERY_URL = os.getenv("FUSEKI_QUERY_URL")
FUSEKI_TIMEOUT_SECONDS = float(os.getenv("FUSEKI_TIMEOUT_SECONDS", "30"))
CORS_ALLOW_ORIGINS = tuple(
	origin.strip()
	for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
	if origin.strip()
)