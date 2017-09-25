# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    ##/##/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by OPENGIS.ch
    email                :    info@opengis.ch
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
import xml.etree.ElementTree as ET

from projectgenerator.libili2db import iliexporter
from projectgenerator.libqgsprojectgen.dataobjects import Project
from projectgenerator.tests.utils import iliexporter_config, testdata_path, rm_file
from qgis.testing import unittest, start_app
from qgis.core import QgsProject, QgsEditFormConfig
from projectgenerator.libqgsprojectgen.generator.postgres import Generator

start_app()


class TestExport(unittest.TestCase):
    def test_export_geopackage(self):
        exporter = iliexporter.Exporter()
        exporter.tool_name = 'ili2gpkg'
        exporter.configuration = iliexporter_config(exporter.tool_name)
        exporter.configuration.base_configuration.custom_model_directories_enabled = testdata_path(
            'ilimodels/CIAF_LADM')
        exporter.configuration.ilimodels = 'CIAF_LADM'
        exporter.configuration.xtffile = testdata_path(
            'xtf/tmp_test_ciaf_ladm.xtf')
        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.print_error)
        self.assertEquals(exporter.run(), iliexporter.Exporter.SUCCESS)
        self.compare_xtfs(testdata_path('xtf/test_ciaf_ladm.xtf'),
                          testdata_path('xtf/tmp_test_ciaf_ladm.xtf'))
        rm_file(testdata_path('xtf/tmp_test_ciaf_ladm.xtf'))

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
            self.assertIsNotNone(tmp_topic)
            print("INFO topic, tmp_topic:", topic.tag, tmp_topic.tag)
            classes = list(topic)
            for _class in classes:
                tmp_class = tmp_topic.find(_class.tag)
                self.assertIsNotNone(tmp_class)
                print("INFO class, tmp_class:", _class.tag, tmp_class.tag)
                for attribute in _class:
                    tmp_attribute = tmp_class.find(attribute.tag)
                    self.assertIsNotNone(tmp_attribute)
                    print("INFO attribute.tag, tmp_attribute.tag:", attribute.tag, tmp_attribute.tag)
                    print("INFO attribute.text, tmp_attribute.text:", attribute.text, tmp_attribute.text)
                    if attribute.tag not in ignored_attributes:
                        self.assertEquals(attribute.text, tmp_attribute.text)


if __name__ == '__main__':
    nose2.main()
