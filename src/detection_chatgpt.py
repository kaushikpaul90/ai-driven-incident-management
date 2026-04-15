# exporter for TF-IDF feature extraction, converting text to numeric form
from sklearn.feature_extraction.text import TfidfVectorizer
# simple linear classifier for logistic regression
from sklearn.linear_model import LogisticRegression
# utility for splitting data into training and test subsets
from sklearn.model_selection import train_test_split
# import here to avoid module-level dependency
from sklearn.metrics import classification_report

# encapsulates the incident detection functionality
class IncidentDetector:

    # initialization of the detector object
    def __init__(self):
        # configure vectorizer with a maximum vocabulary size
        self.vectorizer = TfidfVectorizer(max_features=5000)
        # set up logistic regression with enough iterations for convergence
        self.model = LogisticRegression(max_iter=1000)

    # train the model using provided texts and labels
    def train(self, texts, labels):
        # transform raw texts to TF-IDF feature matrix
        X = self.vectorizer.fit_transform(texts)
        # split the dataset into training and holdout test set
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42
        )

        # fit the classifier on the training data
        self.model.fit(X_train, y_train)

        # return the test split for later evaluation
        return X_test, y_test

    # evaluate on a held-out dataset and print metrics
    def evaluate(self, X_test, y_test):
        # generate predictions from the learned model
        y_pred = self.model.predict(X_test)
        # display detailed precision/recall/f1 results
        print(classification_report(y_test, y_pred))

    # utility to classify new texts after training
    def predict(self, texts):
        # convert texts to feature vectors using fitted vectorizer
        X = self.vectorizer.transform(texts)
        # return predicted labels from the classifier
        return self.model.predict(X)