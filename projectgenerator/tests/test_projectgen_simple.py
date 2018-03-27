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
import psycopg2

from projectgenerator.libqgsprojectgen.dataobjects import Project
from projectgenerator.tests.utils import testdata_path
from qgis.testing import unittest, start_app
from qgis.core import QgsProject, QgsEditFormConfig
from projectgenerator.libqgsprojectgen.generator.generator import Generator

start_app()


class TestProjectGen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_empty_postgres_db(self):
        generator = None
        try:
            generator = Generator('ili2pg', 'dbname=not_exists_database user=docker password=docker host=postgres', 'smart1', '')
            self.assertFalse(True) # must be failed
        except psycopg2.OperationalError as e:
            # psycopg2.OperationalError: FATAL:  database "not_exists_database" does not exist
            self.assertIsNone(generator)

    def test_postgres_db_without_schema(self):
        generator = Generator('ili2pg', 'dbname=gis user=docker password=docker host=postgres', 'smart1')
        self.assertIsNotNone(generator)
        self.assertEqual(len(generator.layers()), 0)

    def test_postgres_db_with_empty_schema(self):
        generator = Generator('ili2pg', 'dbname=gis user=docker password=docker host=postgres', 'smart1', 'empty_schema')
        cur = generator._db_connector.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
        CREATE SCHEMA IF NOT EXISTS empty_schema;
        """)

        self.assertEqual(len(generator.layers()), 0)

    def test_postgres_db_with_not_empty_and_not_interlis_schema(self):
        pass

    def test_empty_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_empty.gpkg'), 'smart2')
        self.assertEqual(len(generator.layers()), 0)

    def test_not_empty_ogr_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_ogr_empty.gpkg'), 'smart2')
        self.assertEqual(len(generator.layers()), 0)

    def test_not_empty_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_relations.gpkg'), 'smart2')
        available_layers = generator.layers()
        relations = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        # https://qgis.org/api/classQgsProject.html
        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)
        self.assertEqual(len(project.layers), 10)
        self.assertEqual(len(project.relations), 1)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)

if __name__ == '__main__':
    nose2.main()
