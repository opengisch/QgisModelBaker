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
import shutil

from qgis.testing import start_app, unittest

import QgisModelBaker.libs.modelbaker.libs.pgserviceparser as pgserviceparser
from QgisModelBaker.gui.panel.pg_config_panel import PgConfigPanel
from QgisModelBaker.libs.modelbaker.db_factory.pg_command_config_manager import (
    PgCommandConfigManager,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.tests.utils import path_testdata

start_app()


class TestPgservice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.pgservicefile = os.environ.get("PGSERVICEFILE", None)
        os.environ["PGSERVICEFILE"] = path_testdata("pgservice/pg_service.conf")

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

    def test_pgservice_settings_remembered(self):
        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        index_postgis_test = pg_config_panel.pg_service_combo_box.findData(
            "postgis_test", PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
        )
        self.assertIsNot(index_postgis_test, -1)

        # Select the pg service and check additional fields' default values
        # e.g., schema
        pg_config_panel.pg_service_combo_box.setCurrentIndex(index_postgis_test)
        self.assertEqual(pg_config_panel.pg_schema_combo_box.currentText(), "")

        # Save to QSettings
        configuration = Ili2DbCommandConfiguration()
        pg_config_panel.get_fields(configuration)
        config_manager = PgCommandConfigManager(configuration)
        config_manager.save_config_in_qsettings()

        # Restart panel and restore QSettings
        pg_config_panel.close()

        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        configuration = Ili2DbCommandConfiguration()  # New config object
        config_manager = PgCommandConfigManager(configuration)
        config_manager.load_config_from_qsettings()
        pg_config_panel.set_fields(configuration)

        # Check PG service settings and additional QSettings
        self.assertEqual(
            pg_config_panel.pg_service_combo_box.currentData(), "postgis_test"
        )
        self.assertEqual(pg_config_panel.pg_host_line_edit.text(), "db.test.com")
        self.assertEqual(pg_config_panel.pg_port_line_edit.text(), "5433")
        self.assertEqual(pg_config_panel.pg_database_line_edit.text(), "postgres")

        self.assertEqual(pg_config_panel.pg_schema_combo_box.currentText(), "")
        self.assertEqual(
            pg_config_panel.pg_ssl_mode_combo_box.currentText(), "verify-ca"
        )
        self.assertEqual(pg_config_panel.pg_auth_settings.password(), "secret")
        self.assertEqual(pg_config_panel.pg_auth_settings.username(), "postgres")

    def test_pgservice_modified_settings_remembered(self):
        # Switch to a copy pg_service.conf
        shutil.copy(
            path_testdata("pgservice/pg_service.conf"),
            path_testdata("pgservice/pg_service_mod.conf"),
        )
        os.environ["PGSERVICEFILE"] = path_testdata("pgservice/pg_service_mod.conf")

        # Remove password setting from the copied pg_service.conf
        config = pgserviceparser.full_config()
        config.remove_option("postgis_test", "password")
        with open(pgserviceparser.conf_path(), "w") as configfile:
            config.write(configfile, space_around_delimiters=False)

        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        index_postgis_test = pg_config_panel.pg_service_combo_box.findData(
            "postgis_test", PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
        )
        self.assertIsNot(index_postgis_test, -1)

        # Select the pg service and check additional fields' default values
        # e.g., schema
        pg_config_panel.pg_service_combo_box.setCurrentIndex(index_postgis_test)
        self.assertEqual(pg_config_panel.pg_schema_combo_box.currentText(), "")

        # This time, set a schema, ssl-mode and password by hand.
        # We'll check that:
        # 1. schema is remembered,
        # 2. ssl-mode will be obtained from the PG service and not from QSettings.
        # 3. password will be obtained from QSettings.
        pg_config_panel.pg_schema_combo_box.setCurrentText("my_schema")
        index = pg_config_panel.pg_ssl_mode_combo_box.findData("require")
        pg_config_panel.pg_ssl_mode_combo_box.setCurrentIndex(index)
        self.assertEqual(pg_config_panel.pg_ssl_mode_combo_box.currentData(), "require")
        pg_config_panel.pg_auth_settings.setPassword("new_secret")

        # Save to QSettings
        configuration = Ili2DbCommandConfiguration()
        pg_config_panel.get_fields(configuration)
        config_manager = PgCommandConfigManager(configuration)
        config_manager.save_config_in_qsettings()

        # Restart panel and restore QSettings
        pg_config_panel.close()

        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        configuration = Ili2DbCommandConfiguration()  # New config object
        config_manager = PgCommandConfigManager(configuration)
        config_manager.load_config_from_qsettings()
        pg_config_panel.set_fields(configuration)

        # Check PG service settings and additional QSettings
        self.assertEqual(
            pg_config_panel.pg_service_combo_box.currentData(), "postgis_test"
        )
        self.assertEqual(pg_config_panel.pg_host_line_edit.text(), "db.test.com")
        self.assertEqual(pg_config_panel.pg_port_line_edit.text(), "5433")
        self.assertEqual(pg_config_panel.pg_database_line_edit.text(), "postgres")

        self.assertEqual(pg_config_panel.pg_schema_combo_box.currentText(), "my_schema")
        self.assertEqual(
            pg_config_panel.pg_ssl_mode_combo_box.currentText(), "verify-ca"
        )
        self.assertEqual(pg_config_panel.pg_auth_settings.password(), "new_secret")
        self.assertEqual(pg_config_panel.pg_auth_settings.username(), "postgres")

        os.environ["PGSERVICEFILE"] = path_testdata("pgservice/pg_service.conf")

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        if cls.pgservicefile:
            os.environ["PGSERVICEFILE"] = cls.pgservicefile

        if os.path.exists(path_testdata("pgservice/pg_service_mod.conf")):
            os.remove(path_testdata("pgservice/pg_service_mod.conf"))
