import pathlib
import os
import pytest
from qgis.testing import unittest
from qgis.PyQt.QtCore import Qt

from QgisModelBaker.libili2db.ilicache import IliCache, IliMetaConfigCache, IliMetaConfigItemModel, IliToppingFileCache, IliToppingFileItemModel
from QgisModelBaker.tests.utils import testdata_path

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

    def test_ilimodels_xml_parser_23(self):
        ilicache = IliCache([])
        ilicache._process_informationfile(os.path.join(test_path, 'testdata', 'ilirepo', '23', 'ilimodels.xml'), 'test_repo', '/testdata/ilirepo/23/ilimodels.xml')
        self.assertIn('test_repo', ilicache.repositories.keys())
        models = set([e['name'] for e in next(elem for elem in ilicache.repositories.values())])
        expected_models =  set(['IliRepository09', 'IliRepository09', 'IliSite09', 'IlisMeta07', 'AbstractSymbology', 'CoordSys', 'RoadsExdm2ben_10', 'RoadsExdm2ien_10', 'RoadsExgm2ien_10', 'StandardSymbology', 'Time', 'Units', 'AbstractSymbology', 'CoordSys', 'RoadsExdm2ben', 'RoadsExdm2ien', 'RoadsExgm2ien', 'StandardSymbology', 'Time', 'Units', 'GM03Core', 'GM03Comprehensive', 'CodeISO', 'GM03_2Core', 'GM03_2Comprehensive', 'CodeISO', 'GM03_2_1Core', 'GM03_2_1Comprehensive', 'IlisMeta07', 'Units', 'IlisMeta07', 'IliRepository09', 'StandardSymbology', 'StandardSymbology', 'GM03Core', 'GM03_2Core', 'GM03_2_1Core', 'CoordSys', 'INTERLIS_ext', 'StandardSymbology', 'INTERLIS_ext', 'IliVErrors', 'RoadsExdm2ien_10', 'RoadsExdm2ien', 'CoordSys', 'StandardSymbology', 'Units', 'Time', 'Time', 'Base', 'Base_f', 'SIA405_Base', 'SIA405_Base_f', 'Base_LV95', 'Base_f_MN95', 'SIA405_Base_LV95', 'SIA405_Base_f_MN95', 'Math', 'Text', 'DatasetIdx16', 'AbstractSymbology', 'AbstractSymbology', 'Time', 'IliRepository20'])
        self.assertEqual(models, expected_models)

    def test_ilimodels_xml_parser_24(self):
        ilicache = IliCache([])
        ilicache._process_informationfile(os.path.join(test_path, 'testdata', 'ilirepo', '24', 'ilimodels.xml'), 'test_repo', '/testdata/ilirepo/24/ilimodels.xml')
        self.assertIn('test_repo', ilicache.repositories.keys())
        models = set([e['name'] for e in next(elem for elem in ilicache.repositories.values())])
        expected_models =  set(['AbstractSymbology', 'CoordSys', 'RoadsExdm2ben', 'RoadsExdm2ien', 'RoadsExgm2ien', 'StandardSymbology', 'Time', 'Units'])
        self.assertEqual(models, expected_models)

    def test_ilimodels_xml_parser_usabilityhub(self):
        ilicache = IliCache([])
        ilicache._process_informationfile(os.path.join(test_path, 'testdata', 'ilirepo', 'usabilityhub', 'ilimodels.xml'), 'usabilityhub', '/testdata/ilirepo/usabilityhub/ilimodels.xml')
        self.assertIn('usabilityhub', ilicache.repositories.keys())
        models = set([e['name'] for e in next(elem for elem in ilicache.repositories.values())])
        expected_models = set(['KbS_LV95_V1_4'])
        self.assertEqual(models, expected_models)

    def test_ilidata_xml_parser_usability_metaconfigfiles(self):
        # find metaconfig file according to the model(s)
        ilimetaconfigcache = IliMetaConfigCache(configuration=None, models='KbS_LV95_V1_4')
        ilimetaconfigcache._process_informationfile(
            os.path.join(test_path, 'testdata', 'ilirepo', 'usabilityhub', 'ilidata.xml'), 'usabilityhub',
            os.path.join(test_path, 'testdata', 'ilirepo', 'usabilityhub'))
        self.assertIn('usabilityhub', ilimetaconfigcache.repositories.keys())
        metaconfigs = set([e['id'] for e in next(elem for elem in ilimetaconfigcache.repositories.values())])
        expected_metaconfigs = {'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0-technical',
                                'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0',
                                'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_localfiletest',
                                'ch.opengis.ili.config.KbS_LV95_V1_4_ili2db',
                                'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0-wrong',
                                'ch.sh.ili.config.KbS_LV95_V1_4_config_V1_0',
                                'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg'}
        self.assertEqual(metaconfigs, expected_metaconfigs)

        ilimetaconfigcache_model = ilimetaconfigcache.model

        matches_on_id = ilimetaconfigcache_model.match(ilimetaconfigcache_model.index(0, 0),
                                                       int(IliMetaConfigItemModel.Roles.ID),
                                                       'ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0', 1,
                                                       Qt.MatchExactly)
        self.assertTrue(matches_on_id)

        if matches_on_id:
            self.assertEqual('Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)',
                             matches_on_id[0].data(Qt.EditRole))
            self.assertEqual('Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)',
                             matches_on_id[0].data(Qt.DisplayRole))
            self.assertEqual('usabilityhub',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.ILIREPO)))
            self.assertEqual('2021-01-06',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.VERSION)))
            self.assertEqual('KbS_LV95_V1_4',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.MODEL)))
            self.assertEqual('metaconfig/opengisch_KbS_LV95_V1_4.ini',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.RELATIVEFILEPATH)))
            self.assertEqual('mailto:david@opengis.ch',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.OWNER)))
            self.assertEqual([{'language': 'de', 'text': 'Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)'}],
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.TITLE)))
            self.assertEqual('ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0',
                             matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.ID)))
            #only check the ending, since it's a absolute path on different plattforms
            self.assertTrue(matches_on_id[0].data(int(IliMetaConfigItemModel.Roles.URL)).endswith(
                'QgisModelBaker/tests/testdata/ilirepo/usabilityhub'))

    def test_ilidata_xml_parser_usability_toppingfiles(self):
        # find qml files according to the ids(s)
        qml_file_ids = ['ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001',
                    'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004',
                    'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005']

        ilitoppingfilecache = IliToppingFileCache(configuration=None, file_ids=qml_file_ids,
                                                  metaconfig_url=os.path.join(test_path,
                                                                              'testdata/ilirepo/usabilityhub/metaconfig/opengisch_KbS_LV95_V1_4.ini'))

        ilitoppingfilecache._process_informationfile(
            os.path.join(test_path, 'testdata', 'ilirepo', 'usabilityhub', 'ilidata.xml'), 'usabilityhub',
            os.path.join(test_path, 'testdata', 'ilirepo', 'usabilityhub'))
        self.assertIn('usabilityhub', ilitoppingfilecache.repositories.keys())
        files = set([e['id'] for e in next(elem for elem in ilitoppingfilecache.repositories.values())])
        expected_files = {'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001',
                    'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004',
                    'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005'}

        self.assertEqual(files, expected_files)

        ilitoppingfilecache_model = ilitoppingfilecache.model

        matches_on_id = ilitoppingfilecache_model.match(ilitoppingfilecache_model.index(0, 0),
                                                        Qt.DisplayRole,
                                                        'ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001', 1,
                                                        Qt.MatchExactly)
        self.assertTrue(matches_on_id)

        if matches_on_id:
            self.assertEqual('ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001',
                             matches_on_id[0].data(Qt.EditRole))
            self.assertEqual('ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001',
                             matches_on_id[0].data(Qt.DisplayRole))
            self.assertEqual('usabilityhub',
                             matches_on_id[0].data(int(IliToppingFileItemModel.Roles.ILIREPO)))
            self.assertEqual('2021-01-20',
                             matches_on_id[0].data(int(IliToppingFileItemModel.Roles.VERSION)))
            self.assertEqual('qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml',
                             matches_on_id[0].data(int(IliToppingFileItemModel.Roles.RELATIVEFILEPATH)))
            #only check the ending, since it's a absolute path on different plattforms
            self.assertTrue(matches_on_id[0].data(int(IliToppingFileItemModel.Roles.LOCALFILEPATH)).endswith(
                'qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml'))
            self.assertEqual('mailto:david@opengis.ch',
                             matches_on_id[0].data(int(IliToppingFileItemModel.Roles.OWNER)))