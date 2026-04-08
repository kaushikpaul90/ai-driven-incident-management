# import functions for loading and preprocessing the BGL dataset
# we pull specific helpers from preprocessing to keep namespace clean
from preprocessing import load_bgl, create_windows
# import the class responsible for training and evaluating incident detectors
from detection import IncidentDetector


# entrypoint for script execution
# wraps the main workflow of loading data, preprocessing, training, and eval

def main():
    # notify user that log loading is about to start
    print("Loading BGL logs...")
    # read raw log contents and corresponding labels from the file system
    contents, labels = load_bgl("../data/BGL.log")

    # inform user that window creation (segmentation) is beginning
    print("Creating windows...")
    # split the sequential log lines into overlapping windows for modeling
    window_texts, window_labels = create_windows(
        contents,
        labels,
        window_size=50,
        stride=10
    )

    # output the number of windows obtained as a sanity check
    print(f"Total windows created: {len(window_texts)}")

    # begin training the incident detection model
    print("Training supervised incident detector...")
    # instantiate the detector object which encapsulates ML logic
    detector = IncidentDetector()
    # train the detector and receive a held-out test set for evaluation
    X_test, y_test = detector.train(window_texts, window_labels)

    # report that evaluation will be performed next
    print("Evaluation Results:")
    # run the evaluation routine on the test split
    detector.evaluate(X_test, y_test)


# Python standard idiom to allow module to be run as a script
if __name__ == "__main__":
    main()