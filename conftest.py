import os

# Run Qt headless in tests: no display / no xvfb needed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
