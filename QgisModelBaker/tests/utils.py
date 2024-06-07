import os

import pytest


@pytest.mark.skip("This is a utility function, not a test function")
def path_testdata(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, "testdata", path)
