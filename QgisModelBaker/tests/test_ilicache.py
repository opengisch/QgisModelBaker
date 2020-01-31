import nose2
import pathlib
import os
from qgis.testing import unittest

from QgisModelBaker.libili2db.ilicache import IliCache


test_path = pathlib.Path(__file__).parent.absolute()
class IliCacheTest(unittest.TestCase):

    def test_modelparser(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsSimpleNoSpace.ili'), 'utf-8')
        self.assertEqual(models[0]['name'], 'RoadsSimple')
        self.assertEqual(models[0]['version'], '2016-08-11')

        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsSimple.ili'), 'utf-8')
        self.assertEqual(models[0]['name'], 'RoadsSimple')
        self.assertEqual(models[0]['version'], '2016-08-11')

        with self.assertRaises(RuntimeError):
            ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsInvalid.ili'), 'utf-8')


if __name__ == '__main__':
    nose2.main()
