# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 09/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import configparser
import datetime
import logging
import os
import pathlib
import shutil
import tempfile

import yaml
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.testing import start_app, unittest

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libili2db.ilicache import IliToppingFileCache
from QgisModelBaker.libqgsprojectgen.dataobjects.project import Project
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from QgisModelBaker.tests.utils import get_pg_connection_string, iliimporter_config

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestProjectTopping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppings_test_path = os.path.join(test_path, "testdata", "ilirepo", "24")

    def importer(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "toml/sh_KbS_LV95_V1_4.toml"
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        result = importer.run()
        return importer, result

    def test_kbs_postgis_qlr_layers(self):
        """
        Checks if layers can be added with a qlr defintion file by the layertree structure.
        """

        importer, result = self.importer()
        assert result == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )
        available_layers = generator.layers()

        assert len(available_layers) == 16

        # load the projecttopping file
        layertree_data_file_path = os.path.join(
            self.toppings_test_path,
            "layertree/opengis_projecttopping_qlr_KbS_LV95_V1_4.yaml",
        )

        with open(layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )

        # "Roads from QLR" layer is appended
        assert len(available_layers) == 17

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check if the ili layers are properly loaded
        ili_layers_group = qgis_project.layerTreeRoot().findGroup(
            "KbS_LV95_V1_4 Layers"
        )
        assert ili_layers_group is not None
        ili_layers_group_layers = ili_layers_group.findLayers()
        assert [layer.name() for layer in ili_layers_group_layers] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
        ]

        # check if the qlr layers are properly loaded
        qlr_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert qlr_layers_group is not None
        qlr_layers_group.findLayers()
        # assert [layer.name() for layer in qlr_layers_group_layers] == [
        #    "The Road Signs",
        # ]

        qlr_group = qlr_layers_group.findGroup("QLR-Group")  # should be "Simple Roads"
        assert qlr_group is not None
        qlr_group.findLayers()
        # assert [layer.name() for layer in qlr_layers_group_layers] == [
        #    "The Road Signs",
        #    etc.
        # ]

    '''
    def test_kbs_postgis_ili_layers(self):
        """
        Checks if the ili_names are set by generator.layers().
        Checks if identificators are set by the layertree structure.
        Checks if layers can be added a second time with a different name by the layertree structure.
        Checks if layers can be added a second time with a different name and be hidden in the project by the layertree structure.
        """

        importer, result = self.importer()
        assert result == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
        )
        available_layers = generator.layers()

        assert [layer.ili_name for layer in available_layers] == [
            "Localisation_V1.MultilingualText",
            "KbS_LV95_V1_4.Belastete_Standorte.Belasteter_Standort",
            "KbS_LV95_V1_4.Belastete_Standorte.Belasteter_Standort",
            "InternationalCodes_V1.LanguageCode_ISO639_1",
            "KbS_Basis_V1_4.Standorttyp",
            "KbS_Basis_V1_4.StatusAltlV",
            "Localisation_V1.LocalisedText",
            "KbS_Basis_V1_4.Deponietyp_",
            "KbS_Basis_V1_4.UntersMassn",
            "Localisation_V1.LocalisedMText",
            "KbS_LV95_V1_4.Belastete_Standorte.ZustaendigkeitKataster",
            "KbS_Basis_V1_4.Parzellenidentifikation",
            "KbS_Basis_V1_4.EGRID_",
            "Localisation_V1.MultilingualMText",
            "KbS_Basis_V1_4.Deponietyp",
            "KbS_Basis_V1_4.UntersMassn_",
        ]

        for layer in available_layers:
            print(f"{len(available_layers)} {layer.name} and {layer.alias}: {layer.ili_name}: \"{layer.geometry_column}\",")

        assert len(available_layers) == 16

        # load the projecttopping file
        layertree_data_file_path = os.path.join(self.toppings_test_path, "layertree/opengis_projecttopping_ili_KbS_LV95_V1_4.yaml")

        with open(layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )

        for layer in available_layers:
            print(f"{len(available_layers)} {layer.name} and {layer.alias}: {layer.ili_name}: \"{layer.geometry_column}\",")

        relations, _ = generator.relations(available_layers)
        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check if the ili layers are properly loaded
        ili_layers_group = qgis_project.layerTreeRoot().findGroup(
            "KbS_LV95_V1_4 Layers"
        )
        assert ili_layers_group is not None
        ili_layers_group_layers = ili_layers_group.findLayers()
        assert [layer.name() for layer in ili_layers_group_layers] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
            "Belasteter_Standort (Renamed)",
        ]
    '''

    '''
    def test_kbs_geopackage_toppings(self):
        """
        Reads this metaconfig found in ilidata.xml according to the modelname KbS_LV95_V1_4

        [CONFIGURATION]
        qgis.modelbaker.layertree=file:tests/testdata/ilirepo/24/layertree/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml
        ch.interlis.referenceData=ilidata:ch.sh.ili.catalogue.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        models = KbS_Basis_V1_4
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml
        preScript=file:tests/testdata/ilirepo/24/sql/opengisch_KbS_LV95_V1_4_test.sql
        defaultSrsCode=3857

        [qgis.modelbaker.qml]
        "Belasteter_Standort"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001
        "Belasteter_Standort (Geo_Lage_Punkt)"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004
        Parzellenidentifikation=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005
        """

        toppings_test_path = os.path.join(test_path, "testdata", "ilirepo", "24")

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, os.path.join(test_path, "testdata", "ilirepo", "24")
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_toppings_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )

        # get the metaconfiguration
        ilimetaconfigcache = IliDataCache(
            configuration=importer.configuration.base_configuration,
            models="KbS_LV95_V1_4",
        )
        ilimetaconfigcache.refresh()
        matches_on_id = ilimetaconfigcache.model.match(
            ilimetaconfigcache.model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg_localfiletest",
            1,
            Qt.MatchExactly,
        )
        assert bool(matches_on_id) is True

        repository = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ILIREPO)
        )
        url = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.URL)
        )
        path = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.RELATIVEFILEPATH)
        )
        dataset_id = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ID)
        )

        metaconfig_path = ilimetaconfigcache.download_file(
            repository, url, path, dataset_id
        )
        metaconfig = self.load_metaconfig(
            os.path.join(toppings_test_path, metaconfig_path)
        )

        # Read ili2db settings
        assert "ch.ehi.ili2db" in metaconfig.sections()
        ili2db_metaconfig = metaconfig["ch.ehi.ili2db"]
        model_list = importer.configuration.ilimodels.strip().split(
            ";"
        ) + ili2db_metaconfig.get("models").strip().split(";")
        importer.configuration.ilimodels = ";".join(model_list)
        assert importer.configuration.ilimodels == "KbS_LV95_V1_4;KbS_Basis_V1_4"
        srs_code = ili2db_metaconfig.get("defaultSrsCode")
        importer.configuration.srs_code = srs_code
        assert importer.configuration.srs_code == "3857"
        command = importer.command(True)
        assert "KbS_LV95_V1_4;KbS_Basis_V1_4" in command
        assert "3857" in command

        # read and download topping files in ili2db settings (prefixed with ilidata or file - means they are found in ilidata.xml or referenced locally)
        ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
        ili_meta_attrs_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, ili_meta_attrs_list
        )
        # absolute path since it's defined as ilidata:...
        expected_ili_meta_attrs_file_path_list = [
            os.path.join(toppings_test_path, "toml/sh_KbS_LV95_V1_4.toml")
        ]
        assert expected_ili_meta_attrs_file_path_list == ili_meta_attrs_file_path_list
        importer.configuration.tomlfile = ili_meta_attrs_file_path_list[0]

        prescript_list = ili2db_metaconfig.get("preScript").split(";")
        prescript_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, prescript_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_prescript_file_path_list = [
            os.path.join(toppings_test_path, "sql/opengisch_KbS_LV95_V1_4_test.sql")
        ]
        assert expected_prescript_file_path_list == prescript_file_path_list
        importer.configuration.pre_script = prescript_file_path_list[0]

        command = importer.command(True)
        assert "opengisch_KbS_LV95_V1_4_test.sql" in command
        assert "sh_KbS_LV95_V1_4.toml" in command

        # and override defaultSrsCode manually
        importer.configuration.srs_code = "2056"

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        # Toppings legend and layers: apply
        assert "CONFIGURATION" in metaconfig.sections()
        configuration_section = metaconfig["CONFIGURATION"]
        assert "qgis.modelbaker.layertree" in configuration_section
        layertree_data_list = configuration_section["qgis.modelbaker.layertree"].split(
            ";"
        )
        layertree_data_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, layertree_data_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_layertree_data_file_path_list = [
            os.path.join(
                toppings_test_path,
                "layertree/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml",
            )
        ]
        assert layertree_data_file_path_list == expected_layertree_data_file_path_list
        layertree_data_file_path = layertree_data_file_path_list[0]

        custom_layer_order_structure = list()
        with open(layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )
            assert "layer-order" in layertree_data
            custom_layer_order_structure = layertree_data["layer-order"]

        assert len(custom_layer_order_structure) == 2

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the legend with layers, groups and subgroups
        belasteter_standort_group = qgis_project.layerTreeRoot().findGroup(
            "Belasteter Standort"
        )
        assert belasteter_standort_group is not None
        belasteter_standort_group_layer = belasteter_standort_group.findLayers()
        assert [layer.name() for layer in belasteter_standort_group_layer] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort",
        ]

        informationen_group = qgis_project.layerTreeRoot().findGroup("Informationen")
        assert informationen_group is not None
        informationen_group_layers = informationen_group.findLayers()

        assert [layer.name() for layer in informationen_group_layers] == [
            "EGRID_",
            "Deponietyp_",
            "ZustaendigkeitKataster",
            "Untersuchungsmassnahmen_Definition",
            "StatusAltlV_Definition",
            "Standorttyp_Definition",
            "Deponietyp_Definition",
            "Parzellenidentifikation",
            "UntersMassn_",
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]

        text_infos_group = informationen_group.findGroup("Text Infos")
        assert text_infos_group is not None
        text_infos_group_layers = text_infos_group.findLayers()
        assert [layer.name() for layer in text_infos_group_layers] == [
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
        ]
        other_infos_group = informationen_group.findGroup("Other Infos")
        assert other_infos_group is not None
        other_infos_group_layers = other_infos_group.findLayers()
        assert [layer.name() for layer in other_infos_group_layers] == [
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]
        # check the node properties
        belasteter_standort_punkt_layer = None
        belasteter_standort_polygon_layer = None
        for layer in belasteter_standort_group_layer:
            if layer.name() == "Belasteter_Standort (Geo_Lage_Punkt)":
                belasteter_standort_punkt_layer = layer
            if layer.name() == "Belasteter_Standort":
                belasteter_standort_polygon_layer = layer
        assert belasteter_standort_punkt_layer is not None
        assert belasteter_standort_polygon_layer is not None
        assert (
            belasteter_standort_punkt_layer.isVisible() is False
        )  # because of yaml setting
        assert (
            belasteter_standort_polygon_layer.isVisible() is True
        )  # because of yaml setting
        assert belasteter_standort_punkt_layer.isExpanded() is False
        assert belasteter_standort_polygon_layer.isExpanded() is True
        assert (
            bool(belasteter_standort_punkt_layer.customProperty("showFeatureCount"))
            is True
        )
        assert (
            bool(belasteter_standort_polygon_layer.customProperty("showFeatureCount"))
            is False
        )
        egrid_layer = None
        zustaendigkeitkataster_layer = None
        for layer in informationen_group_layers:
            if layer.name() == "EGRID_":
                egrid_layer = layer
            if layer.name() == "ZustaendigkeitKataster":
                zustaendigkeitkataster_layer = layer
        assert egrid_layer is not None
        assert zustaendigkeitkataster_layer is not None
        assert bool(egrid_layer.customProperty("showFeatureCount")) is False
        assert (
            bool(zustaendigkeitkataster_layer.customProperty("showFeatureCount"))
            is True
        )
        assert text_infos_group.isExpanded() is True
        assert text_infos_group.isVisible() is False
        assert other_infos_group.isVisible() is True
        assert other_infos_group.isExpanded() is False

        # check the custom layer order
        assert bool(qgis_project.layerTreeRoot().hasCustomLayerOrder()) is True
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[0].name()
            == "Belasteter_Standort"
        )
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[1].name()
            == "Belasteter_Standort (Geo_Lage_Punkt)"
        )

        # and read qml part, download files and check the form configurations set by the qml
        assert "qgis.modelbaker.qml" in metaconfig.sections()
        qml_section = dict(metaconfig["qgis.modelbaker.qml"])
        assert list(qml_section.values()) == [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004_GPKG",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]
        qml_file_model = self.get_topping_file_model(
            importer.configuration.base_configuration, list(qml_section.values())
        )
        for layer in project.layers:
            if layer.alias:
                if any(layer.alias.lower() == s for s in qml_section):
                    layer_qml = layer.alias.lower()
                elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                    layer_qml = f'"{layer.alias.lower()}"'
                else:
                    continue
                matches = qml_file_model.match(
                    qml_file_model.index(0, 0),
                    Qt.DisplayRole,
                    qml_section[layer_qml],
                    1,
                )
                if matches:
                    style_file_path = matches[0].data(
                        int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                    )
                    layer.layer.loadNamedStyle(style_file_path)

        layer_names = set([layer.name for layer in available_layers])
        assert layer_names == {
            "untersuchungsmassnahmen_definition",
            "statusaltlv_definition",
            "untersmassn",
            "deponietyp_definition",
            "parzellenidentifikation",
            "multilingualtext",
            "languagecode_iso639_1",
            "belasteter_standort",
            "zustaendigkeitkataster",
            "deponietyp_",
            "standorttyp",
            "localisedtext",
            "multilingualmtext",
            "untersmassn_",
            "statusaltlv",
            "localisedmtext",
            "standorttyp_definition",
            "egrid_",
            "deponietyp",
            "belasteter_standort_geo_lage_punkt",
        }

        count = 0
        for layer in available_layers:
            if layer.name == "belasteter_standort":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                field_names = set([field.name() for field in tabs[0].children()])
                assert field_names == {
                    "geo_lage_polygon",
                    "bemerkung_de",
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "url_standort",
                    "bemerkung_rm",
                    "standorttyp",
                    "bemerkung_en",
                    "inbetrieb",
                    "geo_lage_punkt",
                    "bemerkung_it",
                    "url_kbs_auszug",
                    "bemerkung",
                    "nachsorge",
                    "ersteintrag",
                    "bemerkung_fr",
                    "katasternummer",
                    "statusaltlv",
                }

                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Bemerkung Romanisch"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Bemerkung Italienisch"
            if layer.name == "parzellenidentifikation":
                count += 1
                assert (
                    layer.layer.displayExpression()
                    == "nbident || ' - '  || \"parzellennummer\" "
                )

        # check if the layers have been considered
        assert count == 2
    '''

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    def load_metaconfig(self, path):
        metaconfig = configparser.ConfigParser()
        metaconfig.clear()
        metaconfig.read_file(open(path))
        metaconfig.read(path)
        return metaconfig

    # that's the same like in generate_project.py
    def get_topping_file_list(self, base_config, id_list):
        topping_file_model = self.get_topping_file_model(base_config, id_list)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, base_config, id_list):
        topping_file_cache = IliToppingFileCache(base_config, id_list)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        return topping_file_cache.model

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
