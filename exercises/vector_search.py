"""Module 1: Vector Search — open the workshop guide at localhost:8080 for guidance."""

from redisvl.query import VectorQuery

from backend.app.bases.rag_base import SimpleRAGBase


class SimpleRAGService(SimpleRAGBase):

    def create_vector_query(self, embedding, rag_config):
        """Build a vector similarity query to search Redis.

        VectorQuery tells Redis: "find me the K closest documents
        to this embedding vector, and return these fields."

        Return a VectorQuery with:
            vector=embedding,
            vector_field_name=rag_config.vector_field,
            return_fields=rag_config.return_fields,
            num_results=???,   # how many documents to retrieve — start with 3
        """
        return None  # Replace with a VectorQuery instance
