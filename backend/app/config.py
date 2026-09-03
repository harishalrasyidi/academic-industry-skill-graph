import os


FUSEKI_QUERY_URL = os.getenv("FUSEKI_QUERY_URL", "http://localhost:3030/myDataset/query")
FUSEKI_TIMEOUT_SECONDS = float(os.getenv("FUSEKI_TIMEOUT_SECONDS", "30"))