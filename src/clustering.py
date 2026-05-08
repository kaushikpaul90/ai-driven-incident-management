from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

class IncidentClusterer:
    def __init__(self, threshold=0.85):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.embeddings = []
        self.threshold = threshold
        self.incidents = []

    def _build_index(self):
        if len(self.embeddings) == 0:
            return

        dim = len(self.embeddings[0])
        self.index = faiss.IndexFlatIP(dim)

        vectors = np.array(self.embeddings).astype("float32")
        faiss.normalize_L2(vectors)

        self.index.add(vectors)

    def is_duplicate(self, text):
        if len(self.embeddings) == 0:
            return False

        vec = self.model.encode([text])[0].astype("float32")
        faiss.normalize_L2(vec.reshape(1, -1))

        scores, _ = self.index.search(vec.reshape(1, -1), k=1)

        return scores[0][0] >= self.threshold

    def add_incident(self, text):
        vec = self.model.encode([text])[0]
        self.embeddings.append(vec)
        self.incidents.append(text)

        self._build_index()