# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 10.08.2021
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
        email                : david at opengis ch
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
import logging
import os
import shutil
import tempfile

from qgis.testing import start_app, unittest

import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.libili2db import iliimporter
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import (
    ilidataimporter_config,
    iliimporter_config,
    testdata_path,
)

start_app()


class TestDatasetHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_import_and_mutation_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OeVBasketTest_V1.ili")
        importer.configuration.ilimodels = "OeVBasketTest"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # Two datasets are created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have four baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # make mutations
        self.check_dataset_mutations(db_connector)

    def test_import_and_mutation_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OeVBasketTest_V1.ili")
        importer.configuration.ilimodels = "OeVBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_basket_gpkg.gpkg"
        )
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # Two datasets are created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have four baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # make mutations
        self.check_dataset_mutations(db_connector)

    def test_import_and_mutation_mssql(self):

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OeVBasketTest_V1.ili")
        importer.configuration.ilimodels = "OeVBasketTest"
        importer.configuration.dbschema = "baskets_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_oevbaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # make mutations
        self.check_dataset_mutations(db_connector)

    def check_dataset_mutations(self, db_connector):
        # Create new dataset
        assert set(
            [record["datasetname"] for record in db_connector.get_datasets_info()]
        ) == {"Winti", "Seuzach"}
        result = db_connector.create_dataset("Glarus Nord")
        assert result[0]
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 4
        assert set(
            [record["datasetname"] for record in db_connector.get_datasets_info()]
        ) == {"Winti", "Seuzach", "Glarus Nord"}

        # Get tid of 'Glarus Nord'
        glarus_nord_tid = [
            record["t_id"]
            for record in db_connector.get_datasets_info()
            if record["datasetname"] == "Glarus Nord"
        ][0]

        # Get topics
        topics = db_connector.get_topics_info()
        assert len(topics) == 2

        # Generate the basket for 'Glarus Nord' and the first topic
        result = db_connector.create_basket(
            glarus_nord_tid, f"{topics[0]['model']}.{topics[0]['topic']}"
        )
        # Generate the basketsfor 'Glarus Nord' and the second topic
        result = db_connector.create_basket(
            glarus_nord_tid, f"{topics[1]['model']}.{topics[1]['topic']}"
        )
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 6

        # Rename dataset
        result = db_connector.rename_dataset(glarus_nord_tid, "Glarus West")
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 6
        assert set(
            [record["datasetname"] for record in db_connector.get_datasets_info()]
        ) == {"Winti", "Seuzach", "Glarus West"}

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
