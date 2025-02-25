from pydantic import BaseModel
from typing import List, Dict, Optional

class UserQuery(BaseModel):
    query: str

class EmbeddingRequest(BaseModel):
    text: str

class PineconeQuery(BaseModel):
    vector: List[float]
    top_k: int = 5

class PineconeStoreRequest(BaseModel):
    id: str
    vector: List[float]
    metadata: Dict[str, Optional[str]] = {}

class CommandRequest(BaseModel):
    command: str
    details: Optional[str] = None

class RoutingDetails(BaseModel):
    Action: str
    Details: Optional[str] = None

class RoutingResponse(BaseModel):
    Message: str
    Routing: RoutingDetails


