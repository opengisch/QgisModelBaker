# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    25/09/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo
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
import nose2
import xml.etree.ElementTree as ET

from projectgenerator.libili2db import (iliexporter,
                                        iliimporter,
                                        ilidataimporter)
from projectgenerator.tests.utils import (iliimporter_config,
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

    def test_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool_name = 'ili2gpkg'
        exporter.configuration = iliexporter_config(exporter.tool_name)
        exporter.configuration.ilimodels = 'CIAF_LADM'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_gpkg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEquals(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ciaf_ladm.xtf'), obtained_xtf_path)

    def _test_export_postgis_empty_schema(self):
        # This test passes without --createBasketCol option in schemaimport 
        # First we need a dbfile with empty tables
        importer_e = iliimporter.Importer()
        importer_e.tool_name = 'ili2pg'
        importer_e.configuration = iliimporter_config(importer_e.tool_name,
                                                      'ilimodels/CIAF_LADM')
        importer_e.configuration.ilimodels = 'CIAF_LADM'
        importer_e.configuration.schema = 'ciaf_ladm_e_{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())
        importer_e.configuration.epsg = 3116
        importer_e.configuration.inheritance = 'smart2'
        importer_e.stdout.connect(self.print_info)
        importer_e.stderr.connect(self.print_error)
        self.assertEquals(importer_e.run(), iliimporter.Importer.SUCCESS)

        exporter_e = iliexporter.Exporter()
        exporter_e.tool_name = 'ili2pg'
        exporter_e.configuration = iliexporter_config(exporter_e.tool_name)
        exporter_e.configuration.ilimodels = 'CIAF_LADM'
        exporter_e.configuration.schema = importer_e.configuration.schema
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_empty.xtf')
        exporter_e.configuration.xtffile = obtained_xtf_path
        exporter_e.stdout.connect(self.print_info)
        exporter_e.stderr.connect(self.print_error)
        self.assertEquals(exporter_e.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_empty_ciaf_ladm.xtf'), obtained_xtf_path)

    def test_export_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name,
                                                    'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEquals(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = ilidataimporter.DataImporter()
        dataImporter.tool_name = 'ili2pg'
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool_name, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'CIAF_LADM'
        dataImporter.configuration.schema = importer.configuration.schema
        dataImporter.configuration.xtffile = testdata_path('xtf/test_ciaf_ladm.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEquals(dataImporter.run(), ilidataimporter.DataImporter.SUCCESS)

        # Export
        exporter = iliexporter.Exporter()
        exporter.tool_name = 'ili2pg'
        exporter.configuration = iliexporter_config(exporter.tool_name)
        exporter.configuration.ilimodels = 'CIAF_LADM'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm_pg.xtf')
        exporter.configuration.xtffile = obtained_xtf_path
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEquals(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path(
            'xtf/test_ciaf_ladm.xtf'), obtained_xtf_path)

    def print_info(self, text):
        print(text)

    def print_error(self, text):
        print(text)

    def compare_xtfs(self, expected, obtained):
        nsxtf = '{http://www.interlis.ch/INTERLIS2.3}'
        ignored_attributes = [nsxtf + 'Comienzo_Vida_Util_Version']
        transfer_root = ET.parse(expected).getroot()
        datasection = transfer_root.find(nsxtf + 'DATASECTION')
        tmp_transfer_root = ET.parse(obtained).getroot()
        tmp_datasection = tmp_transfer_root.find(nsxtf + 'DATASECTION')

        datasection_children = list(datasection)
        tmp_datasection_children = list(tmp_datasection)

        self.assertEquals(len(datasection_children),
                          len(tmp_datasection_children))

        for topic in datasection_children:
            tmp_topic = tmp_datasection.find(topic.tag)
            print("INFO topic, tmp_topic:", topic.tag,
                  tmp_topic.tag if hasattr(tmp_topic, 'tag') else tmp_topic)
            self.assertIsNotNone(tmp_topic)
            classes = list(topic)
            for _class in classes:
                tmp_class = tmp_topic.find(_class.tag)
                print("INFO class, tmp_class:", _class.tag,
                      tmp_class.tag if hasattr(tmp_class, 'tag') else tmp_class)
                self.assertIsNotNone(tmp_class)
                for attribute in _class:
                    tmp_attribute = tmp_class.find(attribute.tag)
                    print("INFO attribute.tag, tmp_attribute.tag:", attribute.tag,
                          tmp_attribute.tag if hasattr(tmp_attribute, 'tag') else tmp_attribute)
                    print("INFO attribute.text, tmp_attribute.text:", attribute.text,
                          tmp_attribute.text if hasattr(tmp_attribute, 'text') else tmp_attribute)
                    self.assertIsNotNone(tmp_attribute)
                    if attribute.tag not in ignored_attributes:
                        self.assertEquals(attribute.text, tmp_attribute.text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)


if __name__ == '__main__':
    nose2.main()
