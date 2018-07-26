# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 28/03/18
        git sha              : :%H$
        copyright            : (C) 2018 by Jorge Useche
        email                : naturalmentejorge@gmail.com
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

from projectgenerator.libqgsprojectgen.dataobjects import Project
from projectgenerator.tests.utils import testdata_path
from qgis.testing import unittest, start_app
from qgis.core import QgsProject, QgsEditFormConfig
from projectgenerator.libqgsprojectgen.generator.generator import Generator

start_app()


class TestProjectGenGenericDatabases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def setUp(self):
        "Run before each test"
        QgsProject.instance().clear()

    def test_empty_postgres_db(self):
        generator = None
        try:
            generator = Generator('ili2pg', 'dbname=not_exists_database user=docker password=docker host=postgres', 'smart1', '')
        except psycopg2.OperationalError as e:
            # psycopg2.OperationalError: FATAL:  database "not_exists_database" does not exist
            self.assertIsNone(generator)

    def test_postgres_db_without_schema(self):
        generator = Generator('ili2pg', 'dbname=gis user=docker password=docker host=postgres', 'smart1')
        self.assertIsNotNone(generator)
        self.assertEqual(len(generator.layers()), 0)

    def test_postgres_db_with_empty_schema(self):
        uri = 'dbname=gis user=docker password=docker host=postgres'
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("CREATE SCHEMA IF NOT EXISTS empty_schema;")

        try:
            generator = Generator('ili2pg', uri, 'smart1', 'empty_schema')
            self.assertEqual(len(generator.layers()), 0)
        finally:
            cur.execute("DROP SCHEMA empty_schema CASCADE;")

    def test_postgis_db_with_non_empty_and_no_interlis_schema_with_spatial_tables(self):
        uri = 'dbname=gis user=docker password=docker host=postgres'
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("CREATE SCHEMA IF NOT EXISTS no_interlis_schema_spatial;")
        try:
            cur.execute("""
                CREATE TABLE no_interlis_schema_spatial.point (
                    id serial NOT NULL,
                    name text,
                    geometry geometry(POINT, 4326) NOT NULL,
                    CONSTRAINT point_id_pkey PRIMARY KEY (id)
                );
                CREATE TABLE no_interlis_schema_spatial.region (
                    id serial NOT NULL,
                    name text,
                    geometry geometry(POLYGON, 4326) NOT NULL,
                    id_point integer,
                    CONSTRAINT region_id_pkey PRIMARY KEY (id)
                );
            """)
            cur.execute("""
                ALTER TABLE no_interlis_schema_spatial.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                REFERENCES no_interlis_schema_spatial.point (id) MATCH FULL
                ON DELETE SET NULL ON UPDATE CASCADE;
            """)
            conn.commit()

            generator = Generator('ili2pg', uri, 'smart1', 'no_interlis_schema_spatial')
            layers = generator.layers()

            self.assertEqual(len(layers), 2)
            relations, foo = generator.relations(layers)
            self.assertEqual(len(relations), 1)

            for layer in layers:
                self.assertIsNotNone(layer.geometry_column)
        finally:
            cur.execute("DROP SCHEMA no_interlis_schema_spatial CASCADE;")
            conn.commit()
            cur.close()

    def test_postgis_db_with_non_empty_and_no_interlis_schema_with_non_spatial_tables(self):
        uri = 'dbname=gis user=docker password=docker host=postgres'
        conn = psycopg2.connect(uri)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("CREATE SCHEMA IF NOT EXISTS no_interlis_schema;")
        try:
            cur.execute("""
                CREATE TABLE no_interlis_schema.point (
                    id serial NOT NULL,
                    name text,
                    CONSTRAINT point_id_pkey PRIMARY KEY (id)
                );
                CREATE TABLE no_interlis_schema.region (
                    id serial NOT NULL,
                    name text,
                    id_point integer,
                    CONSTRAINT region_id_pkey PRIMARY KEY (id)
                );
            """)
            cur.execute("""
                ALTER TABLE no_interlis_schema.region ADD CONSTRAINT region_point_id_point_fk FOREIGN KEY (id_point)
                REFERENCES no_interlis_schema.point (id) MATCH FULL
                ON DELETE SET NULL ON UPDATE CASCADE;
            """)
            conn.commit()

            generator = Generator('ili2pg', uri, 'smart1', 'no_interlis_schema')
            layers = generator.layers()

            self.assertEqual(len(layers), 2)
            relations, foo = generator.relations(layers)
            self.assertEqual(len(relations), 1)

            for layer in layers:
                self.assertIsNone(layer.geometry_column)
        finally:
            cur.execute("DROP SCHEMA no_interlis_schema CASCADE;")
            conn.commit()
            cur.close()

    def test_empty_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_empty.gpkg'), 'smart2')
        self.assertEqual(len(generator.layers()), 0)

    def test_non_empty_ogr_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_ogr_empty.gpkg'), 'smart2')
        self.assertEqual(len(generator.layers()), 0)

    def test_non_empty_geopackage_db(self):
        generator = Generator('ili2gpkg', testdata_path('geopackage/test_relations.gpkg'), 'smart2')
        available_layers = generator.layers()
        relations, foo = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        self.assertEqual(len(qgis_project.mapLayers()), 2)
        self.assertEqual(len(qgis_project.relationManager().relations()), 1)

        for layer in available_layers:
            self.assertIsNotNone(layer.geometry_column)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)

if __name__ == '__main__':
    nose2.main()
