from pinecone import Pinecone
from api.config import settings

# Initialize Pinecone
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)

def search_pinecone(vector: list, top_k: int = 5):
    """Searches the Pinecone index using a vector."""
    try:
        results = pinecone_index.query(
            vector=vector, top_k=top_k, namespace=settings.PINECONE_NAMESPACE, include_metadata=True
        )
        return results
    except Exception as e:
        raise Exception(f"Pinecone search error: {e}")

def store_in_pinecone(id: str, vector: list, metadata: dict = {}):
    """Stores a vector in the Pinecone index."""
    try:
        pinecone_index.upsert(vectors=[{
            "id": id,
            "values": vector,
            "metadata": metadata
        }])
        return {"message": "Vector stored successfully"}
    except Exception as e:
        raise Exception(f"Pinecone store error: {e}")
