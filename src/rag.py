# standard library module for file system operations
import os
# Facebook AI Similarity Search for efficient nearest neighbor retrieval
import faiss
# numerical computing library used for array handling
import numpy as np
# transformer model for generating sentence embeddings
from sentence_transformers import SentenceTransformer

# Retrieval-Augmented Generation engine combining embedding search with documents
class RAGEngine:
    # initialize the RAG engine with a path to a knowledge base directory
    def __init__(self, kb_path):
        # load a lightweight sentence transformer for embeddings
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        # container for raw document texts
        self.documents = []
        # FAISS index instance, to be populated later
        self.index = None
        # load all markdown documents from the knowledge base path
        self.load_documents(kb_path)
        # build the FAISS index after loading documents
        self.build_index()

    def load_documents(self, kb_path):
        self.documents = []
        self.metadata = []

        for root, _, files in os.walk(kb_path):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r") as f:
                        content = f.read()

                    # identify type
                    source_type = "runbook" if "runbooks" in root else "external_doc"

                    # section-based chunking
                    sections = content.split("## ")

                    for section in sections:
                        if not section.strip():
                            continue

                        self.documents.append(section.strip())
                        self.metadata.append({
                            "source": source_type,
                            "filename": file
                        })

        if len(self.documents) == 0:
            raise ValueError("No documents loaded. Check knowledge_base path.")

    # create FAISS index from loaded documents
    def build_index(self):
        # compute embeddings for each document using the transformer
        embeddings = self.model.encode(self.documents)

        if len(embeddings.shape) == 1:
            raise ValueError("Embeddings are empty or invalid. Check document loading.")
    
        # determine vector dimension from embeddings
        dimension = embeddings.shape[1]
        # instantiate a flat (brute-force) L2 index
        self.index = faiss.IndexFlatL2(dimension)
        # add all document vectors to the FAISS index
        self.index.add(np.array(embeddings))

    # retrieve top-k relevant documents for a given query
    def retrieve(self, query, top_k=3):
        # embed the query text in the same vector space
        query_embedding = self.model.encode([query])
        # perform nearest-neighbor search to get distances and indices
        distances, indices = self.index.search(np.array(query_embedding), top_k * 2)
        results = []
        for i in indices[0]:
            results.append({
                "content": self.documents[i],
                "metadata": self.metadata[i]
            })

        # prioritize runbooks
        runbooks = [r for r in results if r["metadata"]["source"] == "runbook"]
        docs = [r for r in results if r["metadata"]["source"] == "external_doc"]

        final = runbooks[:3] + docs[:2]

        return final