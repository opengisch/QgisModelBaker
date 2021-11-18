import os
import pathlib

from qgis.PyQt.QtCore import Qt
from qgis.testing import unittest

from QgisModelBaker.libili2db.ili2dbconfig import BaseConfiguration
from QgisModelBaker.libili2db.ilicache import (
    IliCache,
    IliDataCache,
    IliDataItemModel,
    IliToppingFileCache,
    IliToppingFileItemModel,
)

test_path = pathlib.Path(__file__).parent.absolute()


class IliCacheTest(unittest.TestCase):
    def test_modelparser_v_no_space(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(
            os.path.join(test_path, "testdata", "ilimodels", "RoadsSimpleNoSpace.ili"),
            "utf-8",
        )
        assert models[0]["name"] == "RoadsSimple"
        assert models[0]["version"] == "2016-08-11"

    # Test "!!" line comment
    def test_modelparser_line_comment(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(
            os.path.join(
                test_path, "testdata", "ilimodels", "SIA405_Base_f-20181005.ili"
            ),
            "utf-8",
        )
        assert models[0]["name"] == "SIA405_Base_f"
        assert models[0]["version"] == "05.10.2018"

    def test_modelparser(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(
            os.path.join(test_path, "testdata", "ilimodels", "RoadsSimple.ili"), "utf-8"
        )
        assert models[0]["name"] == "RoadsSimple"
        assert models[0]["version"] == "2016-08-11"

    def test_modelparser_ili1(self):
        ilicache = IliCache([])
        models = ilicache.parse_ili_file(
            os.path.join(test_path, "testdata", "ilimodels", "DM01AVLV95LU2401.ili"),
            "latin1",
        )
        assert models[0]["name"] == "DM01AVLV95LU2401"
        assert models[0]["version"] == ""

    def test_modelparser_invalid(self):
        ilicache = IliCache([])
        with self.assertRaises(RuntimeError):
            ilicache.parse_ili_file(
                os.path.join(test_path, "testdata", "ilimodels", "RoadsInvalid.ili"),
                "utf-8",
            )

    def test_ilimodels_xml_parser_23(self):
        ilicache = IliCache([])
        ilicache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "23", "ilimodels.xml"),
            "test_repo",
            "/testdata/ilirepo/23/ilimodels.xml",
        )
        assert "test_repo" in ilicache.repositories.keys()
        models = set(
            [e["name"] for e in next(elem for elem in ilicache.repositories.values())]
        )
        expected_models = set(
            [
                "IliRepository09",
                "IliRepository09",
                "IliSite09",
                "IlisMeta07",
                "AbstractSymbology",
                "CoordSys",
                "RoadsExdm2ben_10",
                "RoadsExdm2ien_10",
                "RoadsExgm2ien_10",
                "StandardSymbology",
                "Time",
                "Units",
                "AbstractSymbology",
                "CoordSys",
                "RoadsExdm2ben",
                "RoadsExdm2ien",
                "RoadsExgm2ien",
                "StandardSymbology",
                "Time",
                "Units",
                "GM03Core",
                "GM03Comprehensive",
                "CodeISO",
                "GM03_2Core",
                "GM03_2Comprehensive",
                "CodeISO",
                "GM03_2_1Core",
                "GM03_2_1Comprehensive",
                "IlisMeta07",
                "Units",
                "IlisMeta07",
                "IliRepository09",
                "StandardSymbology",
                "StandardSymbology",
                "GM03Core",
                "GM03_2Core",
                "GM03_2_1Core",
                "CoordSys",
                "INTERLIS_ext",
                "StandardSymbology",
                "INTERLIS_ext",
                "IliVErrors",
                "RoadsExdm2ien_10",
                "RoadsExdm2ien",
                "CoordSys",
                "StandardSymbology",
                "Units",
                "Time",
                "Time",
                "Base",
                "Base_f",
                "SIA405_Base",
                "SIA405_Base_f",
                "Base_LV95",
                "Base_f_MN95",
                "SIA405_Base_LV95",
                "SIA405_Base_f_MN95",
                "Math",
                "Text",
                "DatasetIdx16",
                "AbstractSymbology",
                "AbstractSymbology",
                "Time",
                "IliRepository20",
            ]
        )
        assert models == expected_models

    def test_ilimodels_xml_parser_24(self):
        ilicache = IliCache([])
        ilicache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "24", "ilimodels.xml"),
            "test_repo",
            "/testdata/ilirepo/24/ilimodels.xml",
        )
        assert "test_repo" in ilicache.repositories.keys()
        models = set(
            [e["name"] for e in next(elem for elem in ilicache.repositories.values())]
        )
        expected_models = set(
            [
                "AbstractSymbology",
                "CoordSys",
                "RoadsExdm2ben",
                "RoadsExdm2ien",
                "RoadsExgm2ien",
                "StandardSymbology",
                "Time",
                "Units",
            ]
        )
        assert models == expected_models

    def test_ilimodels_xml_parser_24_local_files(self):
        # collects models of a path - means the ones defined in ilimodels.xml and the ones in the ilifiles (if not already in ilimodels.xml) with direct ilidata.xml scan
        ilicache = IliCache([])
        ilicache.process_model_directory(
            os.path.join(test_path, "testdata", "ilirepo", "24")
        )
        assert (
            os.path.join(
                test_path, "testdata", "ilirepo", "24", "additional_local_ili_files"
            )
            in ilicache.repositories.keys()
        )
        models = set(
            [
                model["name"]
                for model in [
                    e for values in ilicache.repositories.values() for e in values
                ]
            ]
        )
        expected_models_of_ilimodels_xml = set(
            [
                "AbstractSymbology",
                "CoordSys",
                "RoadsExdm2ben",
                "RoadsExdm2ien",
                "RoadsExgm2ien",
                "StandardSymbology",
                "Time",
                "Units",
            ]
        )
        expected_models_of_local_ili_files = set(
            [
                "KbS_Basis_V1_4",
                "KbS_LV03_V1_4",
                "KbS_LV95_V1_4",
                "RoadsSimple",
                "Abfallsammelstellen_ZEBA_LV03_V1",
                "Abfallsammelstellen_ZEBA_LV95_V1",
                "DictionariesCH_V1",
                "GeometryCHLV03_V1",
                "S",
                "AdministrativeUnitsCH_V1",
                "CHAdminCodes_V1",
                "Localisation_V1",
                "LE",
                "LocalisationCH_V1",
                "Dictionaries_V1",
                "CatalogueObjectTrees_V1",
                "AdministrativeUnits_V1",
                "GeometryCHLV95_V1",
                "InternationalCodes_V1",
                "CatalogueObjects_V1",
                "PlanerischerGewaesserschutz_LV95_V1_1",
                "PlanerischerGewaesserschutz_LV03_V1_1",
            ]
        )

        assert models == set.union(
            expected_models_of_ilimodels_xml, expected_models_of_local_ili_files
        )

    def test_ilimodels_xml_parser_24_local_repo_local_files(self):
        # collects models of a path - means the ones defined in ilimodels.xml and the ones in the ilifiles (if not already in ilimodels.xml) with local repo scan
        configuration = BaseConfiguration()
        configuration.custom_model_directories_enabled = True
        configuration.custom_model_directories = os.path.join(
            test_path, "testdata", "ilirepo", "24"
        )
        ilicache = IliCache(configuration)
        ilicache.refresh()
        assert (
            os.path.join(
                test_path, "testdata", "ilirepo", "24", "additional_local_ili_files"
            )
            in ilicache.repositories.keys()
        )
        models = set(
            [
                model["name"]
                for model in [
                    e for values in ilicache.repositories.values() for e in values
                ]
            ]
        )
        expected_models_of_ilimodels_xml = set(
            [
                "AbstractSymbology",
                "CoordSys",
                "RoadsExdm2ben",
                "RoadsExdm2ien",
                "RoadsExgm2ien",
                "StandardSymbology",
                "Time",
                "Units",
            ]
        )
        expected_models_of_local_ili_files = set(
            [
                "KbS_Basis_V1_4",
                "KbS_LV03_V1_4",
                "KbS_LV95_V1_4",
                "RoadsSimple",
                "Abfallsammelstellen_ZEBA_LV03_V1",
                "Abfallsammelstellen_ZEBA_LV95_V1",
                "DictionariesCH_V1",
                "GeometryCHLV03_V1",
                "S",
                "AdministrativeUnitsCH_V1",
                "CHAdminCodes_V1",
                "Localisation_V1",
                "LE",
                "LocalisationCH_V1",
                "Dictionaries_V1",
                "CatalogueObjectTrees_V1",
                "AdministrativeUnits_V1",
                "GeometryCHLV95_V1",
                "InternationalCodes_V1",
                "CatalogueObjects_V1",
                "PlanerischerGewaesserschutz_LV95_V1_1",
                "PlanerischerGewaesserschutz_LV03_V1_1",
            ]
        )
        assert models == set.union(
            expected_models_of_ilimodels_xml, expected_models_of_local_ili_files
        )

    def test_ilidata_xml_parser_24_metaconfig_kbs(self):
        # find kbs metaconfig file according to the model(s) with direct ilidata.xml scan
        ilimetaconfigcache = IliDataCache(configuration=None, models="KbS_LV95_V1_4")
        ilimetaconfigcache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "24", "ilidata.xml"),
            "test_repo",
            os.path.join(test_path, "testdata", "ilirepo", "24"),
        )
        assert "test_repo" in ilimetaconfigcache.repositories.keys()
        metaconfigs = set(
            [
                e["id"]
                for e in next(elem for elem in ilimetaconfigcache.repositories.values())
            ]
        )
        expected_metaconfigs = {
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0-technical",
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0",
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_localfiletest",
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg_localfiletest",
            "ch.opengis.ili.config.KbS_LV95_V1_4_ili2db",
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0-wrong",
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg",
        }
        assert metaconfigs == expected_metaconfigs

        ilimetaconfigcache_model = ilimetaconfigcache.model

        matches_on_id = ilimetaconfigcache_model.match(
            ilimetaconfigcache_model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True

        if matches_on_id:
            assert (
                "Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)"
                == matches_on_id[0].data(Qt.EditRole)
            )
            assert (
                "Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)"
                == matches_on_id[0].data(Qt.DisplayRole)
            )
            assert "test_repo" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.ILIREPO)
            )
            assert "2021-01-06" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.VERSION)
            )
            assert (
                "KbS_LV95_V1_4"
                == matches_on_id[0].data(int(IliDataItemModel.Roles.MODELS))[0]
            )
            assert "metaconfig/opengisch_KbS_LV95_V1_4.ini" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.RELATIVEFILEPATH)
            )
            assert "mailto:david@opengis.ch" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.OWNER)
            )
            assert [
                {
                    "language": "de",
                    "text": "Einfaches Styling und Tree und TOML und SH Cat (OPENGIS.ch)",
                }
            ] == matches_on_id[0].data(int(IliDataItemModel.Roles.TITLE))
            assert "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0" == matches_on_id[
                0
            ].data(int(IliDataItemModel.Roles.ID))
            assert os.path.join(
                test_path, "testdata", "ilirepo", "24"
            ) == matches_on_id[0].data(int(IliDataItemModel.Roles.URL))

    def test_ilidata_xml_parser_24_local_repo_metaconfig(self):
        # find planerischerGewaesserschutz metaconfig file according to the model(s) with local repo scan
        configuration = BaseConfiguration()
        configuration.custom_model_directories_enabled = True
        configuration.custom_model_directories = os.path.join(
            test_path, "testdata", "ilirepo", "24"
        )

        ilimetaconfigcache = IliDataCache(
            configuration,
            models="PlanerischerGewaesserschutz_V1;LegendeEintrag_PlanGewaesserschutz_V1_1",
        )
        ilimetaconfigcache.refresh()
        # local repo repository
        assert (
            os.path.join(test_path, "testdata", "ilirepo", "24")
            in ilimetaconfigcache.repositories.keys()
        )

        metaconfigs = set(
            [
                e["id"]
                for e in next(elem for elem in ilimetaconfigcache.repositories.values())
            ]
        )
        expected_metaconfigs = {
            "ch.opengis.ili.config.PlanerischerGewaesserschutz_config",
            "ch.opengis.ili.config.PlanerischerGewaesserschutz_config_localfile",
        }
        assert metaconfigs == expected_metaconfigs

        ilimetaconfigcache_model = ilimetaconfigcache.model

        matches_on_id = ilimetaconfigcache_model.match(
            ilimetaconfigcache_model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.PlanerischerGewaesserschutz_config_localfile",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True

        if matches_on_id:
            assert "Mit lokalem Legendenkatalog" == matches_on_id[0].data(Qt.EditRole)
            assert "Mit lokalem Legendenkatalog" == matches_on_id[0].data(
                Qt.DisplayRole
            )
            assert os.path.join(
                test_path, "testdata", "ilirepo", "24"
            ) == matches_on_id[0].data(int(IliDataItemModel.Roles.ILIREPO))
            assert "2021-03-12" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.VERSION)
            )
            assert (
                "LegendeEintrag_PlanGewaesserschutz_V1_1"
                == matches_on_id[0].data(int(IliDataItemModel.Roles.MODELS))[0]
            )
            assert (
                "metaconfig/opengisch_PlanerischerGewaesserschutz_localfile.ini"
                == matches_on_id[0].data(int(IliDataItemModel.Roles.RELATIVEFILEPATH))
            )
            assert "mailto:david@opengis.ch" == matches_on_id[0].data(
                int(IliDataItemModel.Roles.OWNER)
            )
            assert [
                {"language": "de", "text": "Mit lokalem Legendenkatalog"}
            ] == matches_on_id[0].data(int(IliDataItemModel.Roles.TITLE))
            assert (
                "ch.opengis.ili.config.PlanerischerGewaesserschutz_config_localfile"
                == matches_on_id[0].data(int(IliDataItemModel.Roles.ID))
            )
            assert os.path.join(
                test_path, "testdata", "ilirepo", "24"
            ) == matches_on_id[0].data(int(IliDataItemModel.Roles.URL))

    def test_ilidata_xml_parser_24_linkedmodels(self):
        # find the linked models of PlanerischerGewaesserschutz_LV95_V1_1 (finding it's catalogue opengisch_PlanerischerGewaesserschutz_Codetexte_V1_1 and with it the ModelLink to LegendeEintrag_PlanGewaesserschutz_V1_1)
        # and for GL_Forstreviere_V1 (what is in fact GL_Forstreviere_V1 as well because the catalogue is defined there as well but it's fine for tests.)
        ilireferencedatacache = IliDataCache(
            configuration=None,
            type="referenceData",
            models="PlanerischerGewaesserschutz_LV95_V1_1;GL_Forstreviere_V1",
        )
        ilireferencedatacache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "24", "ilidata.xml"),
            "test_repo",
            os.path.join(test_path, "testdata", "ilirepo", "24"),
        )
        assert "test_repo" in ilireferencedatacache.repositories.keys()
        referencedata = set(
            [
                e["id"]
                for e in next(
                    elem for elem in ilireferencedatacache.repositories.values()
                )
            ]
        )
        expected_referencedata = {
            "ch.opengis.ili.catalogue.PlanerischerGewaesserschutz_Codetexte_V1_1",
            "ch.opengis.ili.catalogue.PlanerischerGewaesserschutz_Codetexte_V1_1_Duplikat",
            "ch.gl.ili.catalogue.GL_Forstreviere_V1_Kataloge",
        }
        assert referencedata == expected_referencedata

        linked_model_list = []
        for r in range(ilireferencedatacache.model.rowCount()):
            if ilireferencedatacache.model.item(r).data(
                int(IliDataItemModel.Roles.MODEL_LINKS)
            ):
                linked_model_list.extend(
                    [
                        model_link.split(".")[0]
                        for model_link in ilireferencedatacache.model.item(r).data(
                            int(IliDataItemModel.Roles.MODEL_LINKS)
                        )
                    ]
                )

        linked_model_set = set(linked_model_list)
        expected_linked_models = {
            "LegendeEintrag_PlanGewaesserschutz_V1_1",
            "GL_Forstreviere_V1",
        }
        assert linked_model_set == expected_linked_models

    def test_ilidata_xml_parser_24_local_repo_linkedmodels(self):
        # find the linked models of PlanerischerGewaesserschutz_LV95_V1_1 (finding it's catalogue opengisch_PlanerischerGewaesserschutz_Codetexte_V1_1 and with it the ModelLink to LegendeEintrag_PlanGewaesserschutz_V1_1)
        # and for GL_Forstreviere_V1 (what is in fact GL_Forstreviere_V1 as well because the catalogue is defined there as well but it's fine for tests.)
        configuration = BaseConfiguration()
        configuration.custom_model_directories_enabled = True
        configuration.custom_model_directories = os.path.join(
            test_path, "testdata", "ilirepo", "24"
        )

        ilireferencedatacache = IliDataCache(
            configuration,
            type="referenceData",
            models="PlanerischerGewaesserschutz_LV95_V1_1;GL_Forstreviere_V1",
        )
        ilireferencedatacache.refresh()
        # local repo repository
        assert (
            os.path.join(test_path, "testdata", "ilirepo", "24")
            in ilireferencedatacache.repositories.keys()
        )

        referencedata = set(
            [
                e["id"]
                for e in next(
                    elem for elem in ilireferencedatacache.repositories.values()
                )
            ]
        )
        expected_referencedata = {
            "ch.opengis.ili.catalogue.PlanerischerGewaesserschutz_Codetexte_V1_1",
            "ch.opengis.ili.catalogue.PlanerischerGewaesserschutz_Codetexte_V1_1_Duplikat",
            "ch.gl.ili.catalogue.GL_Forstreviere_V1_Kataloge",
        }
        assert referencedata == expected_referencedata

        linked_model_list = []
        for r in range(ilireferencedatacache.model.rowCount()):
            if ilireferencedatacache.model.item(r).data(
                int(IliDataItemModel.Roles.MODEL_LINKS)
            ):
                linked_model_list.extend(
                    [
                        model_link.split(".")[0]
                        for model_link in ilireferencedatacache.model.item(r).data(
                            int(IliDataItemModel.Roles.MODEL_LINKS)
                        )
                    ]
                )

        linked_model_set = set(linked_model_list)

        expected_linked_models = {
            "LegendeEintrag_PlanGewaesserschutz_V1_1",
            "GL_Forstreviere_V1",
        }
        assert linked_model_set == expected_linked_models

    def test_ilidata_xml_parser_24_toppingfiles(self):
        # find qml files according to the ids(s) with direct ilidata.xml scan
        qml_file_ids = [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]

        ilitoppingfilecache = IliToppingFileCache(
            configuration=None, file_ids=qml_file_ids
        )

        ilitoppingfilecache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "24", "ilidata.xml"),
            "test_repo",
            os.path.join(test_path, "testdata", "ilirepo", "24"),
        )
        assert "test_repo" in ilitoppingfilecache.repositories.keys()
        files = set(
            [
                e["relative_file_path"]
                for e in next(
                    elem for elem in ilitoppingfilecache.repositories.values()
                )
            ]
        )
        expected_files = {
            "qml/opengisch_KbS_LV95_V1_4_005_parzellenidentifikation.qml",
            "qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml",
            "qml/opengisch_KbS_LV95_V1_4_004_belasteterstandort_punkt.qml",
        }

        assert files == expected_files

        ilitoppingfilecache_model = ilitoppingfilecache.model

        matches_on_id = ilitoppingfilecache_model.match(
            ilitoppingfilecache_model.index(0, 0),
            Qt.DisplayRole,
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True
        if matches_on_id:
            assert (
                "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001"
            ), matches_on_id[0].data(Qt.EditRole)
            assert (
                "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001"
            ), matches_on_id[0].data(Qt.DisplayRole)
            assert "test_repo", matches_on_id[0].data(
                int(IliToppingFileItemModel.Roles.ILIREPO)
            )
            assert "2021-01-20", matches_on_id[0].data(
                int(IliToppingFileItemModel.Roles.VERSION)
            )
            assert (
                "qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml"
                == matches_on_id[0].data(
                    int(IliToppingFileItemModel.Roles.RELATIVEFILEPATH)
                )
            )
            assert (
                os.path.join(
                    test_path,
                    "testdata",
                    "ilirepo",
                    "24",
                    "qml",
                    "opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml",
                )
                == matches_on_id[0].data(
                    int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                )
            )
            assert "mailto:david@opengis.ch" == matches_on_id[0].data(
                int(IliToppingFileItemModel.Roles.OWNER)
            )

    def test_ilidata_xml_parser_24_local_repo_toppingfiles(self):
        # find qml files according to the ids(s) with local repo scan
        qml_file_ids = [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]

        configuration = BaseConfiguration()
        configuration.custom_model_directories_enabled = True
        configuration.custom_model_directories = os.path.join(
            test_path, "testdata", "ilirepo", "24"
        )
        ilitoppingfilecache = IliToppingFileCache(configuration, file_ids=qml_file_ids)
        ilitoppingfilecache.refresh()

        # local repo repository
        assert (
            os.path.join(test_path, "testdata", "ilirepo", "24")
            in ilitoppingfilecache.repositories.keys()
        )
        # local files repository
        assert "local_files" in ilitoppingfilecache.repositories.keys()

        files = set(
            [
                e["relative_file_path"]
                for e in next(
                    elem for elem in ilitoppingfilecache.repositories.values()
                )
            ]
        )
        expected_files = {
            "qml/opengisch_KbS_LV95_V1_4_005_parzellenidentifikation.qml",
            "qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml",
            "qml/opengisch_KbS_LV95_V1_4_004_belasteterstandort_punkt.qml",
        }
        assert files == expected_files

    def test_ilidata_xml_parser_24_local_repo_local_toppingfiles(self):
        # find qml files according to the ids(s) and according to local paths with local repo scan
        qml_file_ids = [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
            "file:qml/opengisch_KbS_LV95_V1_4_005_parzellenidentifikation.qml",
        ]

        configuration = BaseConfiguration()
        configuration.custom_model_directories_enabled = True
        configuration.custom_model_directories = os.path.join(
            test_path, "testdata", "ilirepo", "24"
        )
        ilitoppingfilecache = IliToppingFileCache(configuration, file_ids=qml_file_ids)
        ilitoppingfilecache.refresh()

        # local repo repository
        assert (
            os.path.join(test_path, "testdata", "ilirepo", "24")
            in ilitoppingfilecache.repositories.keys()
        )
        # local files repository
        assert "local_files" in ilitoppingfilecache.repositories.keys()

        files = set(
            [
                e["relative_file_path"]
                for e in next(
                    elem for elem in ilitoppingfilecache.repositories.values()
                )
            ]
        )
        expected_files = {
            "qml/opengisch_KbS_LV95_V1_4_005_parzellenidentifikation.qml",
            "qml/opengisch_KbS_LV95_V1_4_001_belasteterstandort_polygon.qml",
            "qml/opengisch_KbS_LV95_V1_4_004_belasteterstandort_punkt.qml",
            "qml/opengisch_KbS_LV95_V1_4_005_parzellenidentifikation.qml",
        }
        assert files == expected_files

    def test_ilimodels_xml_parser_invalid(self):
        """
        parse invalid models withouth crashing
        """
        ilicache = IliCache([])
        ilicache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "invalid", "ilimodels.xml"),
            "test_repo",
            "/testdata/ilirepo/invalid/ilimodels.xml",
        )
        assert "test_repo" in ilicache.repositories.keys()
        models = set(
            [e["name"] for e in next(elem for elem in ilicache.repositories.values())]
        )
        expected_models = set(["CoordSys", "AbstractSymbology"])
        assert models == expected_models

    def test_ilidata_xml_parser_invalid(self):
        """
        parse invalid data withouth crashing
        """
        ilimetaconfigcache = IliDataCache(configuration=None, models="KbS_LV95_V1_4")
        ilimetaconfigcache._process_informationfile(
            os.path.join(test_path, "testdata", "ilirepo", "invalid", "ilidata.xml"),
            "test_repo",
            os.path.join(test_path, "testdata", "ilirepo", "invalid"),
        )
        assert "test_repo" in ilimetaconfigcache.repositories.keys()
        metaconfigs = set(
            [
                e["id"]
                for e in next(elem for elem in ilimetaconfigcache.repositories.values())
            ]
        )
        # not finding invalid metaconfig but the one with none as id
        expected_metaconfigs = {None, "ch.opengis.ili.config.valid"}
        assert metaconfigs == expected_metaconfigs
