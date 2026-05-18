"""Incident detection training and prediction using a scikit-learn pipeline."""

import os
import joblib
import logging

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

logger = logging.getLogger("incident_pipeline")


class IncidentDetector:
    """Trainable anomaly detector using TF-IDF and logistic regression."""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_dir = os.path.join(base_dir, "models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, "incident_detector.pkl")
        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(max_features=5000, ngram_range=(1, 2)),
                ),
                (
                    "clf",
                    LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0),
                ),
            ]
        )

    def model_exists(self):
        """Return True when a trained detector has been saved."""
        return os.path.exists(self.model_path)

    def save_model(self):
        """Persist the training pipeline to disk."""
        joblib.dump(self.pipeline, self.model_path)

    def load_model(self):
        """Load the saved pipeline from disk."""
        self.pipeline = joblib.load(self.model_path)

    def train(self, texts, labels):
        """Train and save the detector using labeled log windows.

        Args:
            texts (list[str]): Window contents.
            labels (list[int]): Window labels.

        Returns:
            tuple[list[str], list[int]]: Validation set texts and labels.
        """

        logger.info("Training new ML model...")
        X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
        self.pipeline.fit(X_train, y_train)
        self.save_model()
        logger.info("Model saved to: %s", self.model_path)
        return X_test, y_test

    def evaluate(self, X_test, y_test):
        """Log a classification report for the trained detector."""

        from sklearn.metrics import classification_report

        y_pred = self.pipeline.predict(X_test)
        logger.info(classification_report(y_test, y_pred))

    def predict(self, texts):
        """Predict anomaly labels for a list of window texts."""
        return self.pipeline.predict(texts)

    def get_failures(self, texts, labels):
        """Return windows where a true anomaly was missed by the detector."""

        predictions = self.predict(texts)
        return [
            text
            for text, actual, pred in zip(texts, labels, predictions)
            if actual == 1 and pred == 0
        ]
