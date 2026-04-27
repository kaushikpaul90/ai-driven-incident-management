# pandas is included for potential data manipulation needs even if not directly used here
import pandas as pd
# tqdm provides a progress bar wrapper for iterables
from tqdm import tqdm


# split a raw log line into label and message
# input: single line string from BGL
# output: (label, content) tuple

def parse_bgl_line(line):
    """
    Parses one BGL log line.
    Returns:
        label (0 or 1)
        content (log message)
    """
    # split the line on spaces; allow up to 10 segments so message remains intact
    parts = line.split(" ", 9)
    
    # first element is the raw label indicator
    raw_label = parts[0]
    # last element holds the actual log message content
    content = parts[-1]
    
    # Convert the raw label string into a binary indicator
    # '-' denotes normal (0), anything else treated as incident (1)
    label = 0 if raw_label == "-" else 1
    
    # return parsed tuple for further processing
    return label, content


# read an entire BGL log file and parse into lists

def load_bgl(file_path):
    # lists to collect each log message and its label
    contents = []
    labels = []

    # open file safely ignoring encoding errors
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        # iterate through each line with progress reporting
        # for line in tqdm(f):
        for line in f:
            # strip whitespace and parse
            label, content = parse_bgl_line(line.strip())
            # accumulate results
            labels.append(label)
            contents.append(content)

    # return the collected lists to caller
    return contents, labels


# build overlapping windows of log messages for modeling

def create_windows(contents, labels, window_size=50, stride=10):
    # initialize containers for windowed texts and their labels
    window_texts = []
    window_labels = []

    # slide window over the sequence with given stride
    for i in range(0, len(contents) - window_size, stride):
        # capture current window slice
        window = contents[i:i + window_size]
        # determine if any event in window is labeled incident
        window_label = 1 if any(labels[i:i + window_size]) else 0

        # join lines into one string and record label
        window_texts.append(" ".join(window))
        window_labels.append(window_label)

    # output the constructed windows and their respective labels
    return window_texts, window_labels