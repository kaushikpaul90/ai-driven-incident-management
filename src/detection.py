from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

import os
import joblib
import logging

logger = logging.getLogger("incident_pipeline")

class IncidentDetector:

    def __init__(self):

        # ---------------------------------------------------
        # MODEL STORAGE PATH
        # ---------------------------------------------------
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.model_dir = os.path.join(
            BASE_DIR,
            "models"
        )

        os.makedirs(self.model_dir, exist_ok=True)

        self.model_path = os.path.join(
            self.model_dir,
            "incident_detector.pkl"
        )

        # ---------------------------------------------------
        # SKLEARN PIPELINE
        # ---------------------------------------------------
        self.pipeline = Pipeline([
            (
                'tfidf',
                TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2)
                )
            ),
            (
                'clf',
                LogisticRegression(
                    max_iter=1000,
                    class_weight='balanced',
                    C=1.0
                )
            )
        ])

    # ---------------------------------------------------
    # CHECK MODEL EXISTS
    # ---------------------------------------------------
    def model_exists(self):

        return os.path.exists(
            self.model_path
        )

    # ---------------------------------------------------
    # SAVE MODEL
    # ---------------------------------------------------
    def save_model(self):

        joblib.dump(
            self.pipeline,
            self.model_path
        )

    # ---------------------------------------------------
    # LOAD MODEL
    # ---------------------------------------------------
    def load_model(self):

        self.pipeline = joblib.load(
            self.model_path
        )

    # ---------------------------------------------------
    # TRAIN
    # ---------------------------------------------------
    def train(self, texts, labels):

        logger.info(
            "Training new ML model..."
        )

        X_train, X_test, y_train, y_test = (
            train_test_split(
                texts,
                labels,
                test_size=0.2,
                random_state=42
            )
        )

        self.pipeline.fit(
            X_train,
            y_train
        )

        # ---------------------------------------------------
        # SAVE TRAINED MODEL
        # ---------------------------------------------------
        self.save_model()

        logger.info(
            f"Model saved to: {self.model_path}"
        )

        return X_test, y_test

    # ---------------------------------------------------
    # EVALUATE
    # ---------------------------------------------------
    def evaluate(self, X_test, y_test):

        from sklearn.metrics import (
            classification_report
        )

        y_pred = self.pipeline.predict(
            X_test
        )

        logger.info(
            classification_report(
                y_test,
                y_pred
            )
        )

    # ---------------------------------------------------
    # PREDICT
    # ---------------------------------------------------
    def predict(self, texts):

        return self.pipeline.predict(
            texts
        )

    # ---------------------------------------------------
    # FAILURE ANALYSIS
    # ---------------------------------------------------
    def get_failures(
        self,
        texts,
        labels
    ):

        predictions = self.predict(texts)

        failures = []

        for text, actual, pred in zip(
            texts,
            labels,
            predictions
        ):

            if actual == 1 and pred == 0:

                failures.append(text)

        return failures