from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

class IncidentDetector:
    def __init__(self):
        # Using a Pipeline to bundle the steps
        # Added ngram_range for context and 'balanced' weights for the imbalance
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0))
        ])

    def train(self, texts, labels):
        # 1. Split the raw text first (Prevents Data Leakage)
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )

        # 2. Fit the entire pipeline on the training strings
        self.pipeline.fit(X_train, y_train)

        return X_test, y_test

    def evaluate(self, X_test, y_test):
        from sklearn.metrics import classification_report
        y_pred = self.pipeline.predict(X_test)
        print(classification_report(y_test, y_pred))

    def predict(self, texts):
        return self.pipeline.predict(texts)
    
    def get_failures(self, texts, labels):
        """Identifies False Negatives (Incidents missed by the model)"""
        predictions = self.predict(texts)
        failures = []
        
        for text, actual, pred in zip(texts, labels, predictions):
            # Target incidents (1) that the model called normal (0)
            if actual == 1 and pred == 0:
                failures.append(text)
        return failures