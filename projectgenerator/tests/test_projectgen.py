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
import datetime
import shutil
import tempfile
import nose2

from projectgenerator.libili2db import iliimporter
from projectgenerator.libqgsprojectgen.dataobjects import Project
from projectgenerator.tests.utils import iliimporter_config
from qgis.testing import unittest, start_app
from qgis.core import QgsProject, QgsEditFormConfig
from projectgenerator.libqgsprojectgen.generator.generator import Generator

start_app()


class TestProjectGen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            'ili2pg', 'dbname=gis user=docker password=docker host=postgres', 'smart1', importer.configuration.schema)

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
            if layer.name == 'belasteter_standort' and layer.geometry_column == 'geo_lage_punkt':
                belasteter_standort_punkt_layer = layer
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                self.assertEqual(edit_form_config.layout(),
                                 QgsEditFormConfig.TabLayout)
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

                # This might need to be adjusted if we get better names
                self.assertEqual(tabs[1].name(), 'deponietyp_')

            if layer.name == 'belasteter_standort' and layer.geometry_column == 'geo_lage_polygon':
                belasteter_standort_polygon_layer = layer

        self.assertEqual(count, 1)
        self.assertEqual(len(available_layers), 16)

        self.assertGreater(len(qgis_project.relationManager().referencingRelations(belasteter_standort_polygon_layer.layer)), 2)
        self.assertGreater(len(qgis_project.relationManager().referencedRelations(belasteter_standort_polygon_layer.layer)), 3)
        self.assertGreater(len(qgis_project.relationManager().referencingRelations(belasteter_standort_punkt_layer.layer)), 2)
        self.assertGreater(len(qgis_project.relationManager().referencedRelations(belasteter_standort_punkt_layer.layer)), 3)

    def test_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2gpkg'
        importer.configuration = iliimporter_config(importer.tool_name)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg.gpkg')
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2gpkg', importer.configuration.uri, 'smart1')

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
            if layer.name == 'belasteter_standort':  # Polygon
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                self.assertEqual(edit_form_config.layout(),
                                 QgsEditFormConfig.TabLayout)
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
                                              'bemerkung_de']))

                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = ['General',
                                     'parzellenidentifikation',
                                     'belasteter_standort_geo_lage_punkt',
                                     'egrid_',
                                     'deponietyp_',
                                     'untersmassn_']
                self.assertEqual(set(tab_list), set(expected_tab_list))

        self.assertEqual(count, 1)
        self.assertEqual(len(available_layers), 16)

    def test_ranges_postgis(self):
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(
            importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            'ili2pg', 'dbname=gis user=docker password=docker host=postgres', 'smart2', importer.configuration.schema)

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
            if layer.name == 'avaluo':
                config = layer.layer.fields().field('area_terreno2').editorWidgetSetup().config()
                self.assertEqual(config['Min'], '-100.0')
                self.assertEqual(config['Max'], '100000.0')
                count += 1
                break

        self.assertEqual(count, 1)

    def test_ranges_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2gpkg'
        importer.configuration = iliimporter_config(
            importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_gpkg.gpkg')
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator('ili2gpkg', importer.configuration.uri, 'smart2')

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
            if layer.name == 'avaluo':
                config = layer.layer.fields().field('area_terreno2').editorWidgetSetup().config()
                self.assertEqual(config['Min'], '-100.0')
                self.assertEqual(config['Max'], '100000.0')
                count += 1
                break

        self.assertEqual(count, 1)

    def print_info(self, text):
        print(text)

    def print_error(self, text):
        print(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)

if __name__ == '__main__':
    nose2.main()
