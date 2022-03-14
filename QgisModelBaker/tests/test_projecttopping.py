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
        Checks if groups can be added (containing layers itself) with a qlr definition file by the layertree structure.
        Checks if layers can be added with no source info as invalid layers.
        """

        importer, result = self.importer()
        assert result == iliimporter.Importer.SUCCESS

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

        # layers from the qlr group are properly loaded
        qlr_group_layers = qlr_group.findLayers()

        expected_qlr_group_layers = [
            "StreetNamePosition",
            "StreetAxis",
            "LandCover",
            "Street",
            "LandCover_Type",
            "RoadSign_Type",
        ]
        assert (expected_qlr_group_layers) == len(qlr_group_layers)

        # invalid layers are loaded as well
        assert "An invalid layer" in [layer.name() for layer in qlr_layers_group_layers]
        assert "Another invalid layer" in [
            layer.name() for layer in qlr_layers_group_layers
        ]

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
