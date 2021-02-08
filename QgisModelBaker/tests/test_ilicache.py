import pathlib
import os
import pytest
from qgis.testing import unittest

from QgisModelBaker.libili2db.ilicache import IliCache


test_path = pathlib.Path(__file__).parent.absolute()
class IliCacheTest(unittest.TestCase):

    def test_modelparser_v_no_space(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsSimpleNoSpace.ili'), 'utf-8')
        self.assertEqual(models[0]['name'], 'RoadsSimple')
        self.assertEqual(models[0]['version'], '2016-08-11')

    # Test "!!" line comment
    def test_modelparser_line_comment(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'SIA405_Base_f-20181005.ili'), 'utf-8')
        self.assertEqual(models[0]['name'], 'SIA405_Base_f')
        self.assertEqual(models[0]['version'], '05.10.2018')

    def test_modelparser(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsSimple.ili'), 'utf-8')
        self.assertEqual(models[0]['name'], 'RoadsSimple')
        self.assertEqual(models[0]['version'], '2016-08-11')

    def test_modelparser_ili1(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'DM01AVLV95LU2401.ili'), 'latin1')
        self.assertEqual(models[0]['name'], 'DM01AVLV95LU2401')
        self.assertEqual(models[0]['version'], '')

    def test_modelparser_invalid(self):
        ilicache = IliCache([])
        with self.assertRaises(RuntimeError):
            ilicache.parse_ili_file(os.path.join(test_path, 'testdata', 'ilimodels', 'RoadsInvalid.ili'), 'utf-8')

def test_ilimodels_xml_parser_23():
   ilicache = IliCache([])
   ilicache._process_informationfile(os.path.join(test_path, 'testdata', 'ilirepo', '23', 'ilimodels.xml'), 'test_repo')
   assert 'test_repo' in ilicache.repositories.keys()
   models = set([e['name'] for e in next(elem for elem in ilicache.repositories.values())])
   expected_models =  set(['IliRepository09', 'IliRepository09', 'IliSite09', 'IlisMeta07', 'AbstractSymbology', 'CoordSys', 'RoadsExdm2ben_10', 'RoadsExdm2ien_10', 'RoadsExgm2ien_10', 'StandardSymbology', 'Time', 'Units', 'AbstractSymbology', 'CoordSys', 'RoadsExdm2ben', 'RoadsExdm2ien', 'RoadsExgm2ien', 'StandardSymbology', 'Time', 'Units', 'GM03Core', 'GM03Comprehensive', 'CodeISO', 'GM03_2Core', 'GM03_2Comprehensive', 'CodeISO', 'GM03_2_1Core', 'GM03_2_1Comprehensive', 'IlisMeta07', 'Units', 'IlisMeta07', 'IliRepository09', 'StandardSymbology', 'StandardSymbology', 'GM03Core', 'GM03_2Core', 'GM03_2_1Core', 'CoordSys', 'INTERLIS_ext', 'StandardSymbology', 'INTERLIS_ext', 'IliVErrors', 'RoadsExdm2ien_10', 'RoadsExdm2ien', 'CoordSys', 'StandardSymbology', 'Units', 'Time', 'Time', 'Base', 'Base_f', 'SIA405_Base', 'SIA405_Base_f', 'Base_LV95', 'Base_f_MN95', 'SIA405_Base_LV95', 'SIA405_Base_f_MN95', 'Math', 'Text', 'DatasetIdx16', 'AbstractSymbology', 'AbstractSymbology', 'Time', 'IliRepository20'])
   assert models == expected_models

def test_ilimodels_xml_parser_24():
   ilicache = IliCache([])
   ilicache._process_informationfile(os.path.join(test_path, 'testdata', 'ilirepo', '24', 'ilimodels.xml'), 'test_repo')
   assert 'test_repo' in ilicache.repositories.keys()
   models = set([e['name'] for e in next(elem for elem in ilicache.repositories.values())])
   expected_models =  set(['AbstractSymbology', 'CoordSys', 'RoadsExdm2ben', 'RoadsExdm2ien', 'RoadsExgm2ien', 'StandardSymbology', 'Time', 'Units'])

   assert models == expected_models
