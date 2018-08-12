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
import nose2
import psycopg2
import psycopg2.extras

from projectgenerator.libili2db import iliimporter, iliimporter
from projectgenerator.tests.utils import iliimporter_config, ilidataimporter_config, testdata_path
from qgis.testing import unittest, start_app
from qgis import utils

start_app()


class TestImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_import_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool_name = 'ili2pg'
        importer.configuration = iliimporter_config(
            importer.tool_name, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.dbschema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(
            datetime.datetime.now())
        importer.configuration.epsg = 3116
        importer.configuration.inheritance = 'smart2'
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool_name = 'ili2pg'
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool_name, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'CIAF_LADM'
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ciaf_ladm.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Check expected data is there in the database schema
        conn = psycopg2.connect(importer.configuration.uri)

        # Expected predio data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT tipo, st_asText(geometria), st_srid(geometria), t_id
                FROM {}.predio
            """.format(importer.configuration.dbschema))
        record = next(cursor)
        print("INFO", record)
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 'Unidad_Derecho')
        self.assertEqual(record[1], 'POLYGON((1000257.42555766 1002020.37570978,1000437.68843915 1002196.49461698,1000275.4718973 1002428.18956643,1000072.2500615 1002291.5386724,1000158.57171943 1002164.91352262,1000159.94153032 1002163.12799749,1000257.42555766 1002020.37570978))')
        self.assertEqual(record[2], 3116)
        predio_id = record[3]

        # Expected persona data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT documento_numero, nombre, t_id
                FROM {}.persona
            """.format(importer.configuration.dbschema))
        record = next(cursor)
        self.assertIsNotNone(record)
        self.assertEqual(record[0], '1234354656')
        self.assertEqual(record[1], 'Pepito Perez')
        persona_id = record[2]

        # Expected derecho data
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
                SELECT tipo, interesado, unidad
                FROM {}.derecho
            """.format(importer.configuration.dbschema))
        record = next(cursor)
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 'Posesion')
        self.assertEqual(record[1], persona_id)  # FK persona
        self.assertEqual(record[2], predio_id)  # FK predio

    def test_import_geopackage(self):
        # Schema Import
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

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool_name = 'ili2gpkg'
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool_name, 'ilimodels/CIAF_LADM')
        dataImporter.configuration.ilimodels = 'CIAF_LADM'
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            'xtf/test_ciaf_ladm.xtf')
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        self.assertEqual(dataImporter.run(),
                         iliimporter.Importer.SUCCESS)

        # Check expected data is there in the database schema
        conn = utils.spatialite_connect(importer.configuration.dbfile)
        cursor = conn.cursor()
        count = 0

        # Expected predio data
        predio_id = None
        cursor.execute("SELECT tipo, st_srid(geometria), t_id FROM predio")
        for record in cursor:
            count += 1
            self.assertEqual(record[0], 'Unidad_Derecho')
            self.assertEqual(record[1], 3116)
            predio_id = record[2]

        # Expected persona data
        persona_id = None
        cursor.execute("select documento_numero, nombre, t_id from persona")
        for record in cursor:
            count += 1
            self.assertEqual(record[0], '1234354656')
            self.assertEqual(record[1], 'Pepito Perez')
            persona_id = record[2]

        # Expected derecho data
        cursor.execute("select tipo, interesado, unidad from derecho")
        for record in cursor:
            count += 1
            self.assertEqual(record[0], 'Posesion')
            self.assertEqual(record[1], persona_id)
            self.assertEqual(record[2], predio_id)

        self.assertEqual(count, 3)
        cursor.close()
        conn.close()

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
