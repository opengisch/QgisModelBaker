# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    12.03.2018
    git sha              :    :%H$
    copyright            :    (C) 2018 Matthias Kuhn
    email                :    matthias@opengis.ch
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

import logging

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import iliimporter_config, testdata_path, get_pg_connection_string
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from qgis.testing import unittest, start_app
from qgis.core import QgsWkbTypes

start_app()


class TestGeomZ(unittest.TestCase):

    def test_domain_class_relations_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.dbschema = 'exceptional_loads_route'
        importer.configuration.srs_code = 2056
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()

        obstacle_layer = next((layer for layer in available_layers if 'obstacle' in layer.uri))
        obstacle_layer.create()
        self.assertEqual(obstacle_layer.layer.wkbType(), QgsWkbTypes.PointZ)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
