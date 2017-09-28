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

import os
import qgis
import nose2

from projectgenerator.libili2db import iliimporter
from projectgenerator.libqgsprojectgen.dataobjects import Project
from projectgenerator.tests.utils import iliimporter_config, testdata_path
from qgis.testing import unittest, start_app
from qgis.core import QgsProject, QgsEditFormConfig
from projectgenerator.libqgsprojectgen.generator.postgres import Generator

start_app()


class TestProjectGen(unittest.TestCase):
    def test_kbs(self):
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name, None)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.schema = 'kbs'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEquals(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('dbname=gis user=docker password=docker host=postgres', 'kbs', 'smart1')

        available_layers = generator.layers()
        relations = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.table_name == 'belasteter_standort' and layer.geometry_column == 'geo_lage_punkt':
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                self.assertEqual(edit_form_config.layout(), QgsEditFormConfig.TabLayout)
                tabs = edit_form_config.tabs()
                fields = set([field.name() for field in tabs[0].children()])
                self.assertEqual(fields, set(['letzteanpassung',
                                              'zustaendigkeitkataster',
                                              'geo_lage_polygon',
                                              'inbetrieb',
                                              'ersteintrag',
                                              'bemerkung_en',
                                              'bemerkung_rm',
                                              'katasternummer',
                                              'bemerkung_it',
                                              'nachsorge',
                                              'url_kbs_auszug',
                                              'url_standort',
                                              'statusaltlv',
                                              'bemerkung_fr',
                                              'standorttyp',
                                              'bemerkung',
                                              'geo_lage_punkt',
                                              'bemerkung_de']))

                self.assertEqual(tabs[1].name(), 'deponietyp_') # This might need to be adjustet if we get better names

        self.assertEqual(count, 1)
        self.assertEqual(len(available_layers), 16)

    def print_info(self, text):
        print(text)

    def print_error(self, text):
        print(text)

if __name__ == '__main__':
    nose2.main()
