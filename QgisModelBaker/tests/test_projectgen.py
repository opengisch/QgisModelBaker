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
import logging
from decimal import Decimal

from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libqgsprojectgen.dataobjects import Project
from QgisModelBaker.tests.utils import iliimporter_config, testdata_path
from qgis.testing import unittest, start_app
from QgisModelBaker.tests.utils import get_pg_connection_string
from qgis.core import QgsProject, QgsEditFormConfig, QgsRelation
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator
from QgisModelBaker.libqgsprojectgen.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager

start_app()


class TestProjectGen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_ili2db3_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart1', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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

    def test_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart1', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
                                              'katasternummer',
                                              'nachsorge',
                                              'url_kbs_auszug',
                                              'url_standort',
                                              'statusaltlv',
                                              'standorttyp',
                                              'bemerkung',
                                              'bemerkung_de',
                                              'bemerkung_fr',
                                              'bemerkung_rm',
                                              'bemerkung_it',
                                              'bemerkung_en',
                                              'geo_lage_punkt']))

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

    def test_ili2db3_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_kbs_3_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        importer.configuration.db_ili_version = 3
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart1')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        self.assertEqual(tab.columnCount(), 2)
                    else:
                        self.assertEqual(tab.columnCount(), 1)

        self.assertEqual(count, 1)
        self.assertEqual(set(['statusaltlv',
                              'multilingualtext',
                              'untersmassn',
                              'multilingualmtext',
                              'languagecode_iso639_1',
                              'deponietyp',
                              'zustaendigkeitkataster',
                              'standorttyp',
                              'localisedtext',
                              'localisedmtext',
                              'belasteter_standort',
                              'deponietyp_',
                              'egrid_',
                              'untersmassn_',
                              'parzellenidentifikation',
                              'belasteter_standort_geo_lage_punkt']),
                         set([layer.name for layer in available_layers]))

    def test_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'KbS_LV95_V1_3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart1')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
                                              'katasternummer',
                                              'nachsorge',
                                              'url_kbs_auszug',
                                              'url_standort',
                                              'statusaltlv',
                                              'standorttyp',
                                              'bemerkung',
                                              'bemerkung_de',
                                              'bemerkung_fr',
                                              'bemerkung_rm',
                                              'bemerkung_it',
                                              'bemerkung_en']))

                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = ['General',
                                     'parzellenidentifikation',
                                     'belasteter_standort_geo_lage_punkt',
                                     'egrid_',
                                     'deponietyp_',
                                     'untersmassn_']
                self.assertEqual(set(tab_list), set(expected_tab_list))

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        self.assertEqual(tab.columnCount(), 2)
                    else:
                        self.assertEqual(tab.columnCount(), 1)

        self.assertEqual(count, 1)
        self.assertEqual(set(['statusaltlv',
                              'multilingualtext',
                              'untersmassn',
                              'multilingualmtext',
                              'languagecode_iso639_1',
                              'deponietyp',
                              'zustaendigkeitkataster',
                              'standorttyp',
                              'localisedtext',
                              'localisedmtext',
                              'belasteter_standort',
                              'deponietyp_',
                              'egrid_',
                              'untersmassn_',
                              'parzellenidentifikation',
                              'belasteter_standort_geo_lage_punkt']),
                         set([layer.name for layer in available_layers]))

    def test_naturschutz_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'naturschutz_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart1', importer.configuration.dbschema)

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 15)
        self.assertEqual(len(available_layers), 23)
        self.assertEqual(len(relations), 13)

    def test_naturschutz_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart1')

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 24)
        self.assertEqual(len(available_layers), 23)
        self.assertEqual(len(relations), 13)

    def test_naturschutz_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'naturschutz_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2mssql, uri, 'smart1', importer.configuration.dbschema)

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 19)
        self.assertEqual(len(available_layers), 23)
        self.assertEqual(len(relations), 22)

    def test_naturschutz_set_ignored_layers_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'naturschutz_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart1', importer.configuration.dbschema)

        generator.set_additional_ignored_layers(['einzelbaum', 'datenbestand'])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 17)
        self.assertEqual(len(available_layers), 21)
        self.assertEqual(len(relations), 12)

    def test_naturschutz_set_ignored_layers_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart1')

        generator.set_additional_ignored_layers(['einzelbaum', 'datenbestand'])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        legend = generator.legend(available_layers)
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 26)
        self.assertEqual(len(available_layers), 21)
        self.assertEqual(len(relations), 12)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        layer_names = [l.name().lower() for l in qgis_project.mapLayers().values()]
        self.assertNotIn('einzelbaum', layer_names)
        self.assertNotIn('datenbestand', layer_names)
        self.assertIn('hochstamm_obstgarten', layer_names)

    def test_naturschutz_set_ignored_layers_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'
        importer.configuration.dbschema = 'naturschutz_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2mssql, uri, 'smart1', importer.configuration.dbschema)

        generator.set_additional_ignored_layers(['einzelbaum', 'datenbestand'])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 21)
        self.assertEqual(len(available_layers), 21)
        self.assertEqual(len(relations), 21)

    def test_naturschutz_nometa_postgis(self):
        #model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta'
        importer.configuration.dbschema = 'naturschutz_nometa_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart1', importer.configuration.dbschema)

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 9)
        self.assertEqual(len(available_layers), 29)
        self.assertEqual(len(relations), 23)

    def test_naturschutz_nometa_geopackage(self):
        #model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_naturschutz_nometa_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.inheritance = 'smart1'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart1')

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        self.assertEqual(len(ignored_layers), 18)
        self.assertEqual(len(available_layers), 29)
        self.assertEqual(len(relations), 23)

    def test_ranges_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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

                config = layer.layer.fields().field('area_terreno3').editorWidgetSetup().config()
                self.assertEqual(config['Min'], '0.0')
                self.assertEqual(int(Decimal(config['Max'])), 99999999999999)  # '9.9999999999999906e+013'

                count += 1
                break

        self.assertEqual(count, 1)

    def test_ranges_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_ranges_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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

                config = layer.layer.fields().field('area_terreno3').editorWidgetSetup().config()
                self.assertEqual(config['Min'], '0.0')
                self.assertEqual(int(Decimal(config['Max'])), 99999999999999)  # '9.99999999999999E13'

                count += 1
                break

        self.assertEqual(count, 1)


    def test_ranges_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(
            DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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

                config = layer.layer.fields().field('area_terreno3').editorWidgetSetup().config()
                self.assertEqual(config['Min'], '0.0')
                self.assertEqual(int(Decimal(config['Max'])), 99999999999999)  # '99999999999999.9'

                count += 1
                break

        self.assertEqual(count, 1)

    def test_precision_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/RoadsSimpleIndividualExtents.ili')
        importer.configuration.ilimodels = 'RoadsSimple'
        importer.configuration.dbschema = 'roads_simple_prec_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == 'streetnameposition':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.001)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'streetaxis':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.0)
                self.assertFalse(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'roadsign':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.1)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'landcover':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.000001 )
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
        self.assertEqual(count, 4)

    def test_precision_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/RoadsSimpleIndividualExtents.ili')
        importer.configuration.ilimodels = 'RoadsSimple'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_precision_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == 'streetnameposition':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.001)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'streetaxis':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.0)
                self.assertFalse(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'roadsign':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.1)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'landcover':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.000001 )
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
        self.assertEqual(count, 4)

    def test_precision_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/RoadsSimpleIndividualExtents.ili')
        importer.configuration.ilimodels = 'RoadsSimple'
        importer.configuration.dbschema = 'roads_simple_prec_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}' \
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.layer.name().lower() == 'streetnameposition':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.001)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'streetaxis':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.0)
                self.assertFalse(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'roadsign':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.1)
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
            if layer.layer.name().lower() == 'landcover':
                count += 1
                self.assertEqual(layer.extent.toString(),
                                 '0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133')
                self.assertEqual(layer.layer.geometryOptions().geometryPrecision(), 0.000001 )
                self.assertTrue(layer.layer.geometryOptions().removeDuplicateNodes())
        self.assertEqual(count, 4)

    def test_extent_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                self.assertEqual(layer.extent.toString(2), '165000.00,23000.00 : 1806900.00,1984900.00')

        self.assertEqual(count, 1)

    def test_extent_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_extent_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                self.assertEqual(layer.extent.toString(2), '165000.00,23000.00 : 1806900.00,1984900.00')

        self.assertEqual(count, 1)

    def test_extent_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                self.assertEqual(layer.extent.toString(2), '165000.00,23000.00 : 1806900.00,1984900.00')

        self.assertEqual(count, 1)

    def test_nmrel_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'CoordSys'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'geoellipsoidal':
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig('lambert_from5_fkey')
                self.assertEqual(map['nm-rel'], 'lambert_to5_fkey')
                map = edit_form_config.widgetConfig('axis_geoellipsoidal_axis_fkey')
                self.assertFalse(map)
        self.assertEqual(count, 1)

    def test_nmrel_geopackage(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = 'CoordSys'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_nmrel_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'geoellipsoidal':
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig('lambert_from5_geoellipsoidal_T_Id')
                self.assertEqual(map['nm-rel'], 'lambert_to5_geocartesian2d_T_Id')
                map = edit_form_config.widgetConfig('axis_geoellipsoidal_axis_geoellipsoidal_T_Id')
                self.assertFalse(map)
        self.assertEqual(count, 1)

    def test_meta_attr_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"t_id"')

        self.assertEqual(count, 2)

    def test_meta_attr_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'

        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_meta_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"T_Id"')

        self.assertEqual(count, 2)

    def test_meta_attr_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()

        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"T_Id"')

        self.assertEqual(count, 2)

    def test_meta_attr_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.tomlfile = testdata_path('toml/ExceptionalLoadsRoute_V1.toml')
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"t_id"')
            if layer.name == 'obstacle':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')

        self.assertEqual(count, 3)

    def test_meta_attr_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.tomlfile = testdata_path('toml/ExceptionalLoadsRoute_V1.toml')
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"T_Id"')
            if layer.name == 'obstacle':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')

        self.assertEqual(count, 3)

    def test_meta_attr_hidden_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.tomlfile = testdata_path('toml/hidden_fields.toml')
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in project.layers:
            if layer.name == 'predio':
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == 'General':
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        self.assertEqual(len(attribute_names), 18)
                        self.assertNotIn('tipo', attribute_names)
                        self.assertNotIn('avaluo', attribute_names)

        self.assertEqual(count, 1)

    def test_meta_attr_hidden_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.tomlfile = testdata_path('toml/hidden_fields.toml')
        importer.configuration.inheritance = 'smart2'
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in project.layers:
            if layer.name == 'predio':
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == 'General':
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        self.assertEqual(len(attribute_names), 18)
                        self.assertNotIn('tipo', attribute_names)
                        self.assertNotIn('avaluo', attribute_names)

        self.assertEqual(count, 1)

    def test_meta_attr_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ExceptionalLoadsRoute_LV95_V1'
        importer.configuration.tomlfile = testdata_path('toml/ExceptionalLoadsRoute_V1.toml')

        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'typeofroute':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')
            if layer.name == 'route':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), '"T_Id"')
            if layer.name == 'obstacle':
                count += 1
                self.assertEqual(layer.layer.displayExpression(), 'type')

        self.assertEqual(count, 3)

    def test_meta_attr_order_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.tomlfile = testdata_path('toml/attribute_order.toml')

        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_order_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, 'smart2')

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'predio':
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == 'General':
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = ['attr1', 'attr2', 'attr3', 'attr5', 'attr4', 'attr6', 'attr8', 'attr9', 'avaluo', 'tipo', 'fmi', 'numero_predial']

                        for i, val in enumerate(expected_order):
                            self.assertEqual(val, names[i])

        self.assertEqual(count, 1)

    def test_meta_attr_order_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.tomlfile = testdata_path('toml/attribute_order.toml')
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'predio':
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == 'General':
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = ['attr1', 'attr2', 'attr3', 'attr5', 'attr4', 'attr6', 'attr8', 'attr9', 'avaluo', 'tipo', 'fmi', 'numero_predial']

                        for i, val in enumerate(expected_order):
                            self.assertEqual(val, names[i])

        self.assertEqual(count, 1)

    def test_meta_attr_order_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.tomlfile = testdata_path('toml/attribute_order.toml')
        importer.configuration.inheritance = 'smart2'
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}'\
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server="mssql",
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
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
            if layer.name == 'predio':
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == 'General':
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = ['attr1', 'attr2', 'attr3', 'attr5', 'attr4', 'attr6', 'attr8', 'attr9', 'avaluo', 'tipo', 'fmi', 'numero_predial']

                        for i, val in enumerate(expected_order):
                            self.assertEqual(val, names[i])

        self.assertEqual(count, 1)

    def test_bagof_cardinalities_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/CardinalityBag.ili')
        importer.configuration.ilimodels = 'CardinalityBag'
        importer.configuration.dbschema = 'any_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['fische_None', 'valuerelation_0', '0..*', 'ei_typen', 't_id', 'dispname'],
            ['fische_None', 'valuerelation_1', '1..*', 'ei_typen', 't_id', 'dispname']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field],
                              expected_bags_of_enum)

        self.assertEqual(count, 2)

        # Test constraints
        for layer in available_layers:
            if layer.name == 'fische':
                self.assertEqual(
                    layer.layer.constraintExpression(layer.layer.fields().indexOf('valuerelation_0')), '')
                self.assertEqual(
                    layer.layer.constraintExpression(layer.layer.fields().indexOf('valuerelation_1')),
                    'array_length("valuerelation_1")>0')

    def test_bagof_cardinalities_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/CardinalityBag.ili')
        importer.configuration.ilimodels = 'CardinalityBag'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_import_bags_of_enum_CardinalityBag_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ['fische_None', 'valuerelation_0', '0..*', 'ei_typen', 'T_Id', 'dispName'],
            ['fische_None', 'valuerelation_1', '1..*', 'ei_typen', 'T_Id', 'dispName']
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                self.assertIn([layer_name, attribute, cardinality, domain_table.name, key_field, value_field],
                              expected_bags_of_enum)

        self.assertEqual(count, 2)

        # Test constraints
        for layer in available_layers:
            if layer.name == 'fische':
                self.assertEqual(
                    layer.layer.constraintExpression(layer.layer.fields().indexOf('valuerelation_0')), '')
                self.assertEqual(
                    layer.layer.constraintExpression(layer.layer.fields().indexOf('valuerelation_1')),
                    'array_length("valuerelation_1")>0')

    def test_relation_strength_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels//Assoc23.ili')
        importer.configuration.ilimodels = 'Assoc3'
        importer.configuration.dbschema = 'assoc23_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(DbIliMode.ili2pg,
                              get_pg_connection_string(),
                              importer.configuration.inheritance,
                              importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_b_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_b_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg1_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg2_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc1_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc2_a_fkey').strength(), QgsRelation.Association)
        # and that's the one with the strength 1 (composition)
        self.assertEqual(qgis_project.relationManager().relation('classb1_comp1_a_fkey').strength(), QgsRelation.Composition)

    def test_relation_strength_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels//Assoc23.ili')
        importer.configuration.ilimodels = 'Assoc3'
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, 'tmp_assoc23_{:%Y%m%d%H%M%S%f}.gpkg'.format(
                datetime.datetime.now()))
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg,
                              uri,
                              importer.configuration.inheritance)

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_a_classa1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_b_classb1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_a_classa1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_b_classb1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg1_a_classa1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg2_a_classa1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc1_a_classa1_T_Id').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc2_a_classa1_T_Id').strength(), QgsRelation.Association)
        # and that's the one with the strength 1 (composition)
        self.assertEqual(qgis_project.relationManager().relation('classb1_comp1_a_classa1_T_Id').strength(), QgsRelation.Composition)

    def test_relation_strength_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels//Assoc23.ili')
        importer.configuration.ilimodels = 'Assoc3'
        importer.configuration.dbschema = 'assoc23_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        uri = 'DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}' \
            .format(drv="{ODBC Driver 17 for SQL Server}",
                    server=importer.configuration.dbhost,
                    db=importer.configuration.database,
                    uid=importer.configuration.dbusr,
                    pwd=importer.configuration.dbpwd)

        generator = Generator(
            DbIliMode.ili2mssql, uri, 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('agg3_agg3_b_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('assoc3_assoc3_b_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg1_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_agg2_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc1_a_fkey').strength(), QgsRelation.Association)
        self.assertEqual(qgis_project.relationManager().relation('classb1_assoc2_a_fkey').strength(), QgsRelation.Association)
        # and that's the one with the strength 1 (composition)
        self.assertEqual(qgis_project.relationManager().relation('classb1_comp1_a_fkey').strength(), QgsRelation.Composition)

    def test_unit(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, 'ilimodels')
        importer.configuration.ilimodels = 'ZG_Naturschutz_und_Erholungsinfrastruktur_V1'

        importer.configuration.dbschema = 'nue_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        generator = Generator(
            DbIliMode.ili2pg, get_pg_connection_string(), 'smart2', importer.configuration.dbschema)

        available_layers = generator.layers()

        infra_po = next((layer for layer in available_layers if layer.name == 'erholungsinfrastruktur_punktobjekt'))
        naechste_kontrolle = next((field for field in infra_po.fields if field.name == 'naechste_kontrolle'))
        self.assertEqual(naechste_kontrolle.alias, 'Naechste_Kontrolle')

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
