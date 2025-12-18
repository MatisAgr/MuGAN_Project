"""
Configuration constants for the music generation model.

These constants are shared across all modules to ensure consistency
in data representation and model architecture.
"""

MAX_PITCHES = 4
VOCAB_SIZE = 130
NUM_DURATION_CLASSES = 8
NUM_TIME_SHIFT_CLASSES = 9

DURATION_MAP = {
    0: 0.125,
    1: 0.25,
    2: 0.5,
    3: 1.0,
    4: 2.0,
    5: 4.0,
    6: 8.0,
    7: 16.0
}

TIME_SHIFT_MAP = {
    0: 0.0,
    1: 0.0625,
    2: 0.125,
    3: 0.25,
    4: 0.5,
    5: 1.0,
    6: 2.0,
    7: 4.0,
    8: 8.0
}
