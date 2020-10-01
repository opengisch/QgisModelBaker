# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    25/09/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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
import xml.etree.ElementTree as ET
import logging

from QgisModelBaker.libili2db import (iliexporter,
                                        iliimporter)
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import (iliimporter_config,
                                          iliexporter_config,
                                          ilidataimporter_config,
                                          testdata_path)
from qgis.testing import unittest, start_app

start_app()


class TestExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_ili2db3_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2gpkg
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'CIAF_LADM'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_gpkg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.configuration.db_ili_version = 3
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        result = exporter.run()
        if result != iliexporter.Exporter.SUCCESS:
            # failed with a db created by ili2db version 3
            # fallback since of issues with --export3 argument
            # ... and enforce the Exporter to use ili2db version 3.x.x
            exporter.version = 3
            result = exporter.run()
        self.assertEqual(result, iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2gpkg
        exporter.configuration = iliexporter_config(exporter.tool, None, 'geopackage/test_ili2db4_export.gpkg')
        exporter.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;another;ISO19107_V1_MAGNABOG'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_gpkg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ili2db4_ciaf_ladm.xtf'), obtained_xtf_path)

    def _test_export_postgis_empty_schema(self):
        # This test passes without --createBasketCol option in schemaimport
        # First we need a dbfile with empty tables
        importer_e = iliimporter.Importer()
        importer_e.tool = DbIliMode.ili2pg
        importer_e.configuration = iliimporter_config(importer_e.tool,
                                                      'ilimodels/CIAF_LADM')
        importer_e.configuration.ilimodels = 'CIAF_LADM'
        importer_e.configuration.dbschema = 'ciaf_ladm_e_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer_e.configuration.srs_code = 3116
        importer_e.configuration.inheritance = 'smart2'
        importer_e.stdout.connect(self.print_info)
        importer_e.stderr.connect(self.print_error)
        self.assertEqual(importer_e.run(), iliimporter.Importer.SUCCESS)

        exporter_e = iliexporter.Exporter()
        exporter_e.tool = DbIliMode.ili2pg
        exporter_e.configuration = iliexporter_config(exporter_e.tool)
        exporter_e.configuration.ilimodels = 'CIAF_LADM'
        exporter_e.configuration.dbschema = importer_e.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_empty.xtf')
        exporter_e.configuration.xtffile = obtained_xtf_path
        exporter_e.stdout.connect(self.print_info)
        exporter_e.stderr.connect(self.print_error)
        self.assertEqual(exporter_e.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_empty_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_ili2db3_export_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool,
                                                    'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)
        
        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'CIAF_LADM'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ciaf_ladm.xtf')
        dataImporter.configuration.db_ili_version = 3
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2pg
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'CIAF_LADM'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_pg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.configuration.db_ili_version = 3
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        result = exporter.run()
        if result != iliexporter.Exporter.SUCCESS:
            # failed with a db created by ili2db version 3
            # fallback since of issues with --export3 argument
            # ... and enforce the Exporter to use ili2db version 3.x.x
            exporter.version = 3
            result = exporter.run()
        self.assertEqual(result, iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_export_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool,
                                                    'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ili2db4_ciaf_ladm.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2pg
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_pg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ili2db4_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_ili2db3_simple_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2gpkg
        exporter.configuration = iliexporter_config(exporter.tool, None, 'geopackage/test_simple_export.gpkg')
        exporter.configuration.ilimodels = 'RoadsSimple'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_roads_simple_gpkg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.configuration.db_ili_version = 3
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        # don't make a fallback
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_roads_simple.xtf'), obtained_xtf_path)

    def test_simple_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2gpkg
        exporter.configuration = iliexporter_config(exporter.tool, None, 'geopackage/test_ili2db4_simple_export.gpkg')
        exporter.configuration.ilimodels = 'RoadsSimple'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_roads_simple_gpkg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        # don't make a fallback
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_roads_simple.xtf'), obtained_xtf_path)

    def test_ili2db3_simple_export_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/RoadsSimple.ili')
        importer.configuration.ilimodels = 'RoadsSimple'
        importer.configuration.dbschema = 'roads_simple_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = 'RoadsSimple'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_roads_simple.xtf')
        dataImporter.configuration.db_ili_version = 3
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2pg
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'RoadsSimple'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_roads_simple.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.configuration.db_ili_version = 3
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        # don't make a fallback
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_roads_simple.xtf'), obtained_xtf_path)

    def test_ili2db3_simple_export_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            'ilimodels/RoadsSimple.ili')
        importer.configuration.ilimodels = 'RoadsSimple'
        importer.configuration.dbschema = 'roads_simple_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = 'RoadsSimple'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_roads_simple.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2pg
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'RoadsSimple'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_roads_simple.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        # don't make a fallback
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_roads_simple.xtf'), obtained_xtf_path)

    def test_export_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool,
                                                    'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ili2db4_ciaf_ladm.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2mssql
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'Catastro_COL_ES_V2_1_6;CIAF_LADM;ISO19107_V1_MAGNABOG'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_pg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ili2db4_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_ili2db3_export_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool,
                                                    'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'CIAF_LADM'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ciaf_ladm.xtf')
        dataImporter.configuration.db_ili_version = 3
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool = DbIliMode.ili2mssql
        exporter.configuration = iliexporter_config(exporter.tool)
        exporter.configuration.ilimodels = 'CIAF_LADM'
        exporter.configuration.dbschema = importer.configuration.dbschema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_pg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        exporter.version = 3
        self.assertEqual(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ciaf_ladm.xtf'), obtained_xtf_path)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def compare_xtfs(self, expected, obtained):
        nsxtf = '{http://www.interlis.ch/INTERLIS2.3}'
        ignored_child_elements = [nsxtf + 'Comienzo_Vida_Util_Version', nsxtf + 'Geometry']
        transfer_root = ET.parse(expected).getroot()
        datasection = transfer_root.find(nsxtf + 'DATASECTION')
        tmp_transfer_root = ET.parse(obtained).getroot()
        tmp_datasection = tmp_transfer_root.find(nsxtf + 'DATASECTION')

        datasection_children = list(datasection)
        tmp_datasection_children = list(tmp_datasection)

        self.assertEqual(len(datasection_children),
                         len(tmp_datasection_children))

        for topic in datasection_children:
            tmp_topic = tmp_datasection.find(topic.tag)
            self.assertIsNotNone(tmp_topic)
            classes = list(topic)
            for _class in classes:
                success = False
                for _tmp_class in tmp_topic.findall(_class.tag):
                    for child in _class:
                        tmp_child = _tmp_class.find(child.tag)
                        if child.text == tmp_child.text or child.tag in ignored_child_elements:
                            success = True
                        else:
                            success = False
                            break

                    if success:
                        break
                # if same element with same attribute values found, it's true
                self.assertTrue(success)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
