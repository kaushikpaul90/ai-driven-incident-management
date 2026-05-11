# pandas is included for potential data manipulation needs even if not directly used here
from curses import window

import pandas as pd
# tqdm provides a progress bar wrapper for iterables
from tqdm import tqdm


def parse_bgl_line(line):
    """
    Parses one BGL log line.

    Returns:
        label (0 or 1)
        content (FULL ORIGINAL LOG LINE)
    """

    # Preserve full original line
    full_line = line.strip()

    # Empty safety check
    if not full_line:
        return 0, ""

    # First token contains anomaly label
    first_token = full_line.split(" ", 1)[0]

    # '-' means normal log
    label = 0 if first_token == "-" else 1

    # IMPORTANT:
    # Preserve FULL ORIGINAL LOG LINE
    # so timestamps, node IDs, rack IDs,
    # severity and subsystem data survive
    content = full_line

    return label, content


# read an entire BGL log file and parse into lists

def load_bgl(file_path):
    # lists to collect each log message and its label
    contents = []
    labels = []

    # open file safely ignoring encoding errors
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        # iterate through each line with progress reporting
        for line in tqdm(f):
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

        window_records = []

        for log_text, log_label in zip(
            window,
            labels[i:i + window_size]
        ):
            window_records.append({
                "text": log_text,
                "label": log_label
            })

        window_texts.append(window_records)
        window_labels.append(window_label)

    # output the constructed windows and their respective labels
    return window_texts, window_labels