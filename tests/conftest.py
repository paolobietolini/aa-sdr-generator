import logging
import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    yield
    for h in list(root.handlers):
        if h not in original_handlers:
            h.close()
            root.removeHandler(h)
    root.setLevel(original_level)
