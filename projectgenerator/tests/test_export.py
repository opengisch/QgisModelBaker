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
import shutil
import tempfile
import qgis
import nose2
import xml.etree.ElementTree as ET

from projectgenerator.libili2db import iliexporter
from projectgenerator.tests.utils import iliexporter_config, testdata_path
from qgis.testing import unittest, start_app

start_app()


class TestExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests"""
        cls.basetestpath = tempfile.mkdtemp()

    def test_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool_name = 'ili2gpkg'
        exporter.configuration = iliexporter_config(exporter.tool_name)
        exporter.configuration.base_configuration.custom_model_directories_enabled = testdata_path(
            'ilimodels/CIAF_LADM')
        exporter.configuration.ilimodels = 'CIAF_LADM'
        obtained_xtf_path = os.path.join(
            self.basetestpath, 'tmp_test_ciaf_ladm.xtf')
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
        """Run after all tests"""
        shutil.rmtree(cls.basetestpath, True)


if __name__ == '__main__':
    nose2.main()
