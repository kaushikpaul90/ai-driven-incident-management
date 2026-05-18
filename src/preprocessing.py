"""Data loading and window creation utilities for BGL log processing."""

from tqdm import tqdm


def parse_bgl_line(line):
    """Parse a single BGL log line into a label and preserved text.

    Args:
        line (str): One raw line from a BGL log file.

    Returns:
        tuple[int, str]: A binary label (0 normal, 1 anomaly) and the original log text.
    """

    full_line = line.strip()
    if not full_line:
        return 0, ""

    first_token = full_line.split(" ", 1)[0]
    label = 0 if first_token == "-" else 1
    return label, full_line


def load_bgl(file_path):
    """Load a BGL file and return its log lines and labels.

    Args:
        file_path (str): Path to the BGL log file.

    Returns:
        tuple[list[str], list[int]]: All log lines and their anomaly labels.
    """

    contents = []
    labels = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as stream:
        for line in tqdm(stream, desc="Loading BGL logs"):
            label, content = parse_bgl_line(line)
            labels.append(label)
            contents.append(content)
    return contents, labels


def create_windows(contents, labels, window_size=50, stride=10):
    """Build overlapping log windows for model training and detection.

    Args:
        contents (list[str]): Ordered log lines.
        labels (list[int]): Corresponding anomaly labels.
        window_size (int): Number of lines per window.
        stride (int): Step size between windows.

    Returns:
        tuple[list[list[dict[str, int|str]]], list[int]]: Window records and window labels.
    """

    window_texts = []
    window_labels = []

    for i in range(0, len(contents) - window_size, stride):
        window = contents[i : i + window_size]
        window_label = 1 if any(labels[i : i + window_size]) else 0
        window_records = [
            {"text": text, "label": label}
            for text, label in zip(window, labels[i : i + window_size])
        ]
        window_texts.append(window_records)
        window_labels.append(window_label)
    return window_texts, window_labels
