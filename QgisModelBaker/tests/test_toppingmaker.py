import os
import pathlib
import tempfile

from qgis.testing import unittest

import QgisModelBaker.internal_libs.projecttopping.projecttopping as toppingmaker

test_path = pathlib.Path(__file__).parent.absolute()


class ToppingMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppingmaker_test_path = os.path.join(test_path, "toppingmaker")

    def test_target(self):
        maindir = os.path.join(self.toppingmaker_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        filedirs = ["projecttopping", "layerstyle", "layerdefinition", "andanotherone"]
        target = toppingmaker.Target("freddys", maindir, subdir, filedirs)
        target.makedirs()
        count = 0
        for filedir in filedirs:
            assert os.path.isdir(filedir)
            count += 1
        assert count == 4
