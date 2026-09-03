from pydantic import BaseModel, Field


class SparqlQueryRequest(BaseModel):
    query: str = Field(min_length=1)