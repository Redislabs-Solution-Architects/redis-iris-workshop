"""Module 1: Vector Search — Reference Solution."""

from redisvl.query import VectorQuery

from backend.app.bases.rag_base import SimpleRAGBase


class SimpleRAGService(SimpleRAGBase):

    def create_vector_query(self, embedding, rag_config):
        return VectorQuery(
            vector=embedding,
            vector_field_name=rag_config.vector_field,
            return_fields=rag_config.return_fields,
            num_results=rag_config.num_results,
        )
