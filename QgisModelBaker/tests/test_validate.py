# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08.12.2021
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

from QgisModelBaker.gui.validate import ValidationResultModel
from QgisModelBaker.libili2db import iliimporter, ilivalidator
from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.tests.utils import (
    ilidataimporter_config,
    iliimporter_config,
    ilivalidator_config,
    testdata_path,
)

start_app()


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_validate_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_roads_simple_validation_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbfile = importer.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS

        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(ValidationResultModel.Roles.MESSAGE)[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def test_validate_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2pg
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbschema = importer.configuration.dbschema
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS
        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(ValidationResultModel.Roles.MESSAGE)[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def test_validate_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2mssql
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbschema = importer.configuration.dbschema
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS
        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(ValidationResultModel.Roles.MESSAGE)[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
