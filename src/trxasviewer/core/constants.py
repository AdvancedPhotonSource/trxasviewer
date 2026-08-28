# Copyright © UChicago Argonne LLC
# See LICENSE file for details
# Map from time unit label to scale factor (relative to seconds)
TIME_SCALES = {"ns": 1e-9, "µs": 1e-6, "ms": 1e-3, "s": 1}

# Inverse map: scale factor → time unit label
SCALE_TO_TIME = {v: k for k, v in TIME_SCALES.items()}
