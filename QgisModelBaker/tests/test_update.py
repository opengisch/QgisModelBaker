import datetime
import logging
import os

import pyodbc
import psycopg2
import psycopg2.extras
import shutil
import tempfile

from QgisModelBaker.libili2db import iliupdater, iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from qgis.testing import unittest, start_app
from qgis import utils

from QgisModelBaker.libqgsprojectgen.db_factory.mssql_command_config_manager import MssqlCommandConfigManager
from QgisModelBaker.libqgsprojectgen.db_factory.pg_command_config_manager import PgCommandConfigManager
from QgisModelBaker.tests.utils import iliimporter_config, iliupdater_config, testdata_path


start_app()


class TestUpdate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.base_test_path = tempfile.mkdtemp()

    def test_update_postgis(self):
        tool = DbIliMode.ili2pg
        dataset_name = 'updater_test'
        schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())

        importer = self.__get_importer(tool)
        importer.configuration.dbschema = schema

        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        updater = self.__get_updater(tool, dataset_name)
        updater.configuration.dbschema = schema

        self.assertEqual(updater.run(), iliupdater.Updater.SUCCESS)

        config_manager = PgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        conn = psycopg2.connect(uri)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check expected data is there in the database schema
        self.__check_updater(dataset_name, cursor, schema)

        cursor.close()
        conn.close()

    def test_update_mssql(self):
        tool = DbIliMode.ili2mssql
        dataset_name = 'updater_test'
        schema = 'ciaf_ladm_{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())

        importer = self.__get_importer(tool)
        importer.configuration.dbschema = schema

        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        updater = self.__get_updater(tool, dataset_name)
        updater.configuration.dbschema = schema

        self.assertEqual(updater.run(), iliupdater.Updater.SUCCESS)

        config_manager = MssqlCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        conn = pyodbc.connect(uri)
        cursor = conn.cursor()

        # Check expected data is there in the database schema
        self.__check_updater(dataset_name, cursor, schema)

        cursor.close()
        conn.close()

    def test_update_gpkg(self):
        tool = DbIliMode.ili2gpkg
        dataset_name = 'updater_test'
        db_file = os.path.join(self.base_test_path, 'tmp_update_gpkg.gpkg')

        importer = self.__get_importer(tool)
        importer.configuration.dbfile = db_file
        self.assertEqual(importer.run(), iliimporter.Importer.SUCCESS)

        updater = self.__get_updater(tool, dataset_name)
        updater.configuration.dbfile = db_file
        self.assertEqual(updater.run(), iliupdater.Updater.SUCCESS)

        conn = utils.spatialite_connect(importer.configuration.dbfile)
        cursor = conn.cursor()

        self.__check_updater(dataset_name, cursor)

        cursor.close()
        conn.close()

    def __get_importer(self, tool):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = tool
        importer.configuration = iliimporter_config(tool, 'ilimodels/CIAF_LADM')
        importer.configuration.ilimodels = 'CIAF_LADM'
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = 'smart2'
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        return importer

    def __get_updater(self, tool, dataset_name):
        updater = iliupdater.Updater()
        updater.tool = tool
        updater.configuration = iliupdater_config(tool, 'ilimodels/CIAF_LADM')
        updater.configuration.dataset = dataset_name
        updater.configuration.with_importbid = True
        updater.configuration.with_importtid = True
        updater.configuration.xtffile = testdata_path('xtf/test_ciaf_ladm.xtf')

        updater.stdout.connect(self.print_info)
        updater.stderr.connect(self.print_error)

        return updater

    def __check_updater(self, dataset_name, cursor, schema=None):
        schema = schema + '.' if schema else ''

        # check_expected dataset
        cursor.execute("""
              SELECT T_Id, datasetName
              FROM {}T_ILI2DB_DATASET
            """.format(schema))
        record = next(cursor)
        self.assertIsNotNone(record)
        t_id_dataset = record[0]
        self.assertEqual(record[1], dataset_name)

        # check --importBID
        expected_basket_name = 'CIAF_LADM.Catastro'

        cursor.execute("""SELECT T_Id, T_Ili_Tid 
            FROM {}T_ILI2DB_BASKET WHERE dataset={}""".format(schema, t_id_dataset))

        record = next(cursor)
        self.assertIsNotNone(record)
        t_id_basket = record[0]
        self.assertEqual(record[1], expected_basket_name)

        # check --importTID
        expected_t_ili_tid = '1'

        cursor.execute("""SELECT T_Ili_Tid 
            FROM {}avaluo WHERE T_basket = {}""".format(schema, t_id_basket))

        record = next(cursor)
        self.assertIsNotNone(record)
        self.assertEqual(record[0], expected_t_ili_tid)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.base_test_path, True)
