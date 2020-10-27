from QgisModelBaker.libili2db.ili2dbutils import get_all_modeldir_in_path
from QgisModelBaker.tests.utils import testdata_path
from qgis.testing import unittest


class TestILI2DBUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.parent_dir = testdata_path('')
        cls.ilimodels = testdata_path('ilimodels')
        cls.ciaf_ladm = testdata_path('ilimodels/CIAF_LADM')
        cls.empty = testdata_path('ilimodels/subparent_dir/empty')
        cls.hidden = testdata_path('ilimodels/subparent_dir/.hidden')
        cls.not_hidden = testdata_path('ilimodels/subparent_dir/not_hidden')
        cls.not_modeldir = testdata_path('xtf')

    def test_parse_subdirs_in_parent_dir(self):
        modeldirs = get_all_modeldir_in_path(self.parent_dir)  # Parent folder: testdata
        expected_dirs = [self.ilimodels, self.ciaf_ladm, self.hidden, self.not_hidden]
        self.assertEqual(sorted(expected_dirs), sorted(modeldirs.split(";")))

    def test_parse_subdirs_in_hidden_dir(self):
        modeldirs = get_all_modeldir_in_path(self.hidden)
        self.assertEqual(self.hidden, modeldirs)

    def test_parse_subdirs_in_not_hidden_dir(self):
        modeldirs = get_all_modeldir_in_path(self.not_hidden)
        self.assertEqual(self.not_hidden, modeldirs)

    def test_parse_subdirs_in_empty_dir(self):
        modeldirs = get_all_modeldir_in_path(self.empty)
        self.assertEqual('', modeldirs)

    def test_parse_subdirs_in_not_model_dir(self):
        modeldirs = get_all_modeldir_in_path(self.not_modeldir)
        self.assertEqual('', modeldirs)