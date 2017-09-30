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

import datetime
import shutil
import nose2
import psycopg2
import psycopg2.extras

from projectgenerator.libili2db import iliimporter, ilidataimporter
from projectgenerator.tests.utils import iliimporter_config, ilidataimporter_config, testdata_path
from qgis.testing import unittest, start_app

start_app()


class TestImport(unittest.TestCase):

    def test_import_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(importer.tool_name, 'ilimodels/CIAF_LADM')
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

        # Check expected data is there in the database schema
        conn = psycopg2.connect(importer.configuration.uri)

        # Expected predio data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT tipo, st_asText(geometria), st_srid(geometria), t_id
                FROM {}.predio
            """.format(importer.configuration.schema))
        record = next(cursor)
        print("INFO", record)
        self.assertIsNotNone(record)
        self.assertEquals(record[0], 'Unidad_Derecho')
        self.assertEquals(record[1], 'POLYGON((1000257.42555766 1002020.37570978,1000437.68843915 1002196.49461698,1000275.4718973 1002428.18956643,1000072.2500615 1002291.5386724,1000158.57171943 1002164.91352262,1000159.94153032 1002163.12799749,1000257.42555766 1002020.37570978))')
        self.assertEquals(record[2], 3116)
        predio_id = record[3]

        # Expected persona data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT documento_numero, nombre, t_id
                FROM {}.persona
            """.format(importer.configuration.schema))
        record = next(cursor)
        print("INFO", record)
        self.assertIsNotNone(record)
        self.assertEquals(record[0], '1234354656')
        self.assertEquals(record[1], 'Pepito Perez')
        persona_id = record[2]

        # Expected derecho data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT tipo, interesado, unidad
                FROM {}.derecho
            """.format(importer.configuration.schema))
        record = next(cursor)
        print("INFO", record)
        self.assertIsNotNone(record)
        self.assertEquals(record[0], 'Posesion')
        self.assertEquals(record[1], persona_id) # FK persona
        self.assertEquals(record[2], predio_id) # FK predio

    def print_info(self, text):
        print(text)

    def print_error(self, text):
        print(text)


if __name__ == '__main__':
    nose2.main()
