"""
/***************************************************************************
    begin                :    15/03/2022
    git sha              :    :%H$
    copyright            :    (C) 2022 by Damiano Lombardi
    email                :    damiano@opengis.ch
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

from qgis.testing import start_app, unittest

from QgisModelBaker.gui.panel.pg_config_panel import PgConfigPanel
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.tests.utils import testdata_path

start_app()


class TestPgservice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.pgservicefile = os.environ.get("PGSERVICEFILE", None)
        os.environ["PGSERVICEFILE"] = testdata_path("pgservice/pg_service.conf")

    def test_pgservice_pg_config_panel(self):

        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        index_postgis_test = pg_config_panel.pg_service_combo_box.findData(
            "postgis_test", PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
        )
        self.assertIsNot(index_postgis_test, -1)

        configuration = Ili2DbCommandConfiguration()
        configuration.dbservice = "postgis_test"
        pg_config_panel.set_fields(configuration)
        pg_config_panel.get_fields(configuration)

        self.assertEqual(configuration.dbhost, "db.test.com")
        self.assertEqual(configuration.dbport, "5433")
        self.assertEqual(configuration.dbusr, "postgres")
        self.assertEqual(configuration.dbpwd, "secret")
        self.assertEqual(configuration.sslmode, "verify-ca")

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        if cls.pgservicefile:
            os.environ["PGSERVICEFILE"] = cls.pgservicefile
