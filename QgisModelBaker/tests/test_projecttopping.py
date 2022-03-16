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

import datetime
import logging
import os
import pathlib
import shutil
import tempfile

import yaml
from qgis.core import QgsProject
from qgis.testing import start_app, unittest

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
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

    def test_kbs_postgis_qlr_layers(self):
        """
        Checks if layers can be added with a qlr defintion file by the layertree structure.
        Checks if groups can be added (containing layers itself) with a qlr definition file by the layertree structure.
        Checks if layers can be added with no source info as invalid layers.
        """

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
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
            path_resolver=lambda path: os.path.join(self.toppings_test_path, path)
            if path
            else None,
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

        # QLR defined layer ("Roads from QLR") is appended
        # layers from QLR defined group are not
        # invalid layers ("An invalid layer" and "Another invalid layer") are appended
        assert len(available_layers) == 19

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

        qlr_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert qlr_layers_group is not None

        # qlr layer ("Roads from QLR") is properly loaded
        qlr_layers_group_layers = qlr_layers_group.findLayers()
        assert "The Road Signs" in [layer.name() for layer in qlr_layers_group_layers]

        # qlr group ("QLR-Group") is properly loaded
        qlr_group = qlr_layers_group.findGroup("Simple Roads")
        assert qlr_group is not None

        qlr_group_layers = qlr_group.findLayers()
        expected_qlr_layers = {
            "StreetNamePosition",
            "StreetAxis",
            "LandCover",
            "Street",
            "LandCover_Type",
            "RoadSign_Type",
            "The Road Signs",
        }
        assert set([layer.name() for layer in qlr_group_layers]) == expected_qlr_layers

    def test_kbs_postgis_source_layers(self):
        """
        Checks if layers can be added with "ogr" provider and uri defined in the layertree structure.
        Checks if layers can be added with "postgres" provider and uri defined in the layertree structure.
        Checks if layers can be added with "wms" provider and uri defined in the layertree structure.
        Checks if layers can be added with no source info as invalid layers.
        """

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
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
            path_resolver=lambda path: os.path.join(self.toppings_test_path, path)
            if path
            else None,
        )
        available_layers = generator.layers()

        assert len(available_layers) == 16

        # load the projecttopping file
        layertree_data_file_path = os.path.join(
            self.toppings_test_path,
            "layertree/opengis_projecttopping_source_KbS_LV95_V1_4.yaml",
        )

        # write dynamic parameters in the new file
        test_layertree_data_file_path = os.path.join(
            test_path, "testtree_{:%Y%m%d%H%M%S%f}.yaml".format(datetime.datetime.now())
        )
        with open(layertree_data_file_path, "r") as file:
            filedata = file.read()

            filedata = filedata.replace("{test_path}", os.path.join(test_path))
            filedata = filedata.replace("{PGHOST}", importer.configuration.dbhost)
            filedata = filedata.replace(
                "{test_schema}", importer.configuration.dbschema
            )

            with open(test_layertree_data_file_path, "w") as file:
                file.write(filedata)

        with open(test_layertree_data_file_path, "r") as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )

        # ogr layer is added ("Local Landcover")
        # postgres layer is added ("Local Belasteter Standort")
        # wms layer is added ("Local WMS")
        # invalid layers ("An invalid layer" and "Another invalid layer") are appended
        assert len(available_layers) == 21

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

        source_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert source_layers_group is not None

        # ogr layer ("Local Landcover") is properly loaded
        source_layers_group_layers = source_layers_group.findLayers()
        expected_source_layers = {
            "Local Landcover",
            "Local Zuständigkeit Kataster",
            "Local WMS",
            "An invalid layer",
            "Another invalid layer",
        }
        assert (
            set([layer.name() for layer in source_layers_group_layers])
            == expected_source_layers
        )

        for layer in source_layers_group_layers:
            qgis_layer = layer.layer()
            if layer.name() == "Local WMS":
                assert qgis_layer.dataProvider().name() == "wms"
                print(qgis_layer.dataProvider().dataSourceUri())
                assert (
                    qgis_layer.dataProvider().dataSourceUri()
                    == "contextualWMSLegend=0&crs=EPSG:2056&dpiMode=7&featureCount=10&format=image/jpeg&layers=ch.bav.kataster-belasteter-standorte-oev_lines&styles=default&url=https://wms.geo.admin.ch/?%0ASERVICE%3DWMS%0A%26VERSION%3D1.3.0%0A%26REQUEST%3DGetCapabilities"
                )
                assert qgis_layer.isValid()
            if layer.name() == "Local Zuständigkeit Kataster":
                assert qgis_layer.dataProvider().name() == "postgres"
                print(qgis_layer.dataProvider().dataSourceUri())
                assert (
                    qgis_layer.dataProvider().dataSourceUri()
                    == f"dbname='gis' host={importer.configuration.dbhost} user='docker' password='docker' key='t_id' checkPrimaryKeyUnicity='1' table=\"{importer.configuration.dbschema}\".\"zustaendigkeitkataster\""
                )
                assert qgis_layer.isValid()
            if layer.name() == "Local Landcover":
                assert qgis_layer.dataProvider().name() == "ogr"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)