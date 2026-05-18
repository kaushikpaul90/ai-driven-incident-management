"""Retrieval-Augmented Generation engine using FAISS and embeddings."""

import os
import numpy as np
import faiss
from embedding_client import EmbeddingClient


class RAGEngine:
    """Load KB documents, build an embedding index, and retrieve relevant text."""

    def __init__(self, kb_path):
        self.embedding_client = EmbeddingClient()
        self.documents = []
        self.metadata = []
        self.index = None
        self.load_documents(kb_path)
        self.build_index()

    def load_documents(self, kb_path):
        """Read markdown files from the KB directory and store document chunks."""

        self.documents = []
        self.metadata = []

        for root, _, files in os.walk(kb_path):
            for file_name in files:
                if not file_name.endswith(".md"):
                    continue

                file_path = os.path.join(root, file_name)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as stream:
                    content = stream.read()

                source_type = "runbook" if "runbooks" in root else "external_doc"
                sections = content.split("## ")
                for section in sections:
                    section_text = section.strip()
                    if not section_text:
                        continue
                    self.documents.append(section_text)
                    self.metadata.append({"source": source_type, "filename": file_name})

        if not self.documents:
            raise ValueError("No documents loaded. Check knowledge_base path.")

    def build_index(self):
        """Embed loaded documents and add them to a FAISS index."""

        embeddings = self.embedding_client.embed_texts(self.documents)
        embeddings = np.array(embeddings)
        if embeddings.ndim != 2:
            raise ValueError("Embeddings are empty or invalid. Check document loading.")

        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query, top_k=3):
        """Return the most relevant documents for a query."""

        safe_query = query
        if getattr(self.embedding_client, "provider", None) == "azure":
            max_chars = 8000
            if len(query) > max_chars:
                safe_query = query[:max_chars]

        query_embedding = self.embedding_client.embed_texts([safe_query])
        distances, indices = self.index.search(np.array(query_embedding), top_k * 2)

        results = [
            {"content": self.documents[i], "metadata": self.metadata[i]}
            for i in indices[0]
        ]

        runbooks = [item for item in results if item["metadata"]["source"] == "runbook"]
        docs = [item for item in results if item["metadata"]["source"] != "runbook"]
        return runbooks[:3] + docs[:2]
