"""
/***************************************************************************
    begin                :    23/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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

import logging
from enum import IntEnum

import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError
from qgis.PyQt.QtCore import Qt, pyqtSignal

import QgisModelBaker.libs.modelbaker.libs.pgserviceparser as pgserviceparser
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.libs.modelbaker.utils.qt_utils import (
    NonEmptyStringValidator,
    Validators,
)
from QgisModelBaker.utils import gui_utils

from .db_config_panel import DbConfigPanel

WIDGET_UI = gui_utils.get_ui_class("pg_settings_panel.ui")


class PgConfigPanel(DbConfigPanel, WIDGET_UI):
    """Panel where users fill out connection parameters to Postgres/Postgis database.

    :cvar notify_fields_modified: Signal that is called when any field is modified.
    :type notify_field_modified: pyqtSignal(str)
    """

    class _SERVICE_COMBOBOX_ROLE(IntEnum):
        DBSERVICE = Qt.UserRole
        DBHOST = Qt.UserRole + 1
        DBPORT = Qt.UserRole + 2
        DBUSR = Qt.UserRole + 3
        DATABASE = Qt.UserRole + 4
        DBSCHEMA = Qt.UserRole + 5
        DBPWD = Qt.UserRole + 6
        DBAUTHID = Qt.UserRole + 7
        SSLMODE = Qt.UserRole + 8

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)
        self.setupUi(self)

        self._current_service = None

        from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
            BaseConfiguration,
        )

        self.pg_use_super_login.setText(
            self.tr(
                "Execute data management tasks with superuser login from settings ({})"
            ).format(BaseConfiguration().super_pg_user)
        )
        self.pg_use_super_login.setToolTip(
            self.tr(
                "Data management tasks are <ul><li>Create the schema</li><li>Read meta information</li><li>Import data from XTF</li><li>Export data to XTF</li></ul>"
            )
        )

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)
        self.pg_schema_combo_box.setValidator(nonEmptyValidator)

        self.pg_schema_combo_box.setEditable(True)

        self.pg_host_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.pg_database_line_edit.textChanged.emit(self.pg_database_line_edit.text())
        self.pg_schema_combo_box.lineEdit().textChanged.connect(
            self.validators.validate_line_edits
        )

        self.pg_host_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_port_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_database_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_schema_combo_box.currentTextChanged.connect(self.notify_fields_modified)

        # Fill pg_services combo box
        self.pg_service_combo_box.addItem(self.tr("None"), None)
        for service in pgserviceparser.service_names():
            self.pg_service_combo_box.addItem(service, service)

        self.pg_service_combo_box.currentIndexChanged.connect(
            self._pg_service_combo_box_changed
        )

        # Fill sslmode combo box
        self.pg_ssl_mode_combo_box.addItem("none", None)
        self.pg_ssl_mode_combo_box.addItem("disable", "disable")
        self.pg_ssl_mode_combo_box.addItem("allow", "allow")
        self.pg_ssl_mode_combo_box.addItem("prefer", "prefer")
        self.pg_ssl_mode_combo_box.addItem("require", "require")
        self.pg_ssl_mode_combo_box.addItem("verify-ca", "verify-ca")
        self.pg_ssl_mode_combo_box.addItem("verify-full", "verify-full")

        self.pg_ssl_mode_combo_box.setItemData(
            0, self.tr("Do not set the sslmode parameter"), Qt.ToolTipRole
        )
        self.pg_ssl_mode_combo_box.setItemData(
            1, self.tr("Only try a non-SSL connection"), Qt.ToolTipRole
        )
        self.pg_ssl_mode_combo_box.setItemData(
            2,
            self.tr(
                "First try a non-SSL connection; if that fails, try an SSL connection"
            ),
            Qt.ToolTipRole,
        )
        self.pg_ssl_mode_combo_box.setItemData(
            3,
            self.tr(
                "First try an SSL connection; if that fails, try a non-SSL connection"
            ),
            Qt.ToolTipRole,
        )
        self.pg_ssl_mode_combo_box.setItemData(
            4,
            self.tr(
                "Only try an SSL connection. If a root CA file is present, verify the certificate in the same way as if verify-ca was specified"
            ),
            Qt.ToolTipRole,
        )
        self.pg_ssl_mode_combo_box.setItemData(
            5,
            self.tr(
                "Only try an SSL connection, and verify that the server certificate is issued by a trusted certificate authority (CA)"
            ),
            Qt.ToolTipRole,
        )
        self.pg_ssl_mode_combo_box.setItemData(
            6,
            self.tr(
                "Only try an SSL connection, verify that the server certificate is issued by a trusted CA and that the requested server host name matches that in the certificate"
            ),
            Qt.ToolTipRole,
        )

        self._show_panel()

    def _show_panel(self):

        self._fill_schema_combo_box()

        if (
            self._db_action_type == DbActionType.GENERATE
            or self._db_action_type == DbActionType.IMPORT_DATA
        ):
            self.pg_schema_combo_box.setPlaceholderText(self.tr("Schema Name"))
        elif self._db_action_type == DbActionType.EXPORT:
            self.pg_schema_combo_box.setPlaceholderText(
                self.tr("[Enter a valid schema]")
            )
        else:
            logging.error(f"Unknown action type: {self._db_action_type}")

    def get_fields(self, configuration):

        configuration.dbservice = self.pg_service_combo_box.currentData()
        configuration.dbhost = self.pg_host_line_edit.text().strip()
        configuration.dbport = self.pg_port_line_edit.text().strip()
        configuration.dbusr = self.pg_auth_settings.username()
        configuration.database = self.pg_database_line_edit.text().strip()
        configuration.dbschema = self.pg_schema_combo_box.currentText().strip().lower()
        configuration.dbpwd = self.pg_auth_settings.password()
        configuration.dbauthid = self.pg_auth_settings.configId()

        configuration.sslmode = self.pg_ssl_mode_combo_box.currentData()

        configuration.db_use_super_login = self.pg_use_super_login.isChecked()

    def set_fields(self, configuration):

        if configuration.dbservice is None:

            indexNoService = self.pg_service_combo_box.findData(
                None, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbhost,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBHOST,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbport,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPORT,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbusr,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBUSR,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.database,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DATABASE,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbschema,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSCHEMA,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbpwd,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPWD,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.dbauthid,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBAUTHID,
            )
            self.pg_service_combo_box.setItemData(
                indexNoService,
                configuration.sslmode,
                PgConfigPanel._SERVICE_COMBOBOX_ROLE.SSLMODE,
            )

        self.pg_host_line_edit.setText(configuration.dbhost)
        self.pg_port_line_edit.setText(configuration.dbport)
        self.pg_auth_settings.setUsername(configuration.dbusr)
        self.pg_database_line_edit.setText(configuration.database)
        self.pg_schema_combo_box.setCurrentText(configuration.dbschema)
        self.pg_auth_settings.setPassword(configuration.dbpwd)
        self.pg_auth_settings.setConfigId(configuration.dbauthid)

        index = self.pg_ssl_mode_combo_box.findData(configuration.sslmode)
        self.pg_ssl_mode_combo_box.setCurrentIndex(index)

        self.pg_use_super_login.setChecked(configuration.db_use_super_login)

        index = self.pg_service_combo_box.findData(configuration.dbservice)
        self.pg_service_combo_box.setCurrentIndex(index)

    def is_valid(self):
        result = False
        message = ""
        if not self.pg_host_line_edit.text().strip():
            message = self.tr("Please set a host before creating the project.")
            self.pg_host_line_edit.setFocus()
        elif not self.pg_database_line_edit.text().strip():
            message = self.tr("Please set a database before creating the project.")
            self.pg_database_line_edit.setFocus()
        elif (
            not self.pg_auth_settings.username()
            and not self.pg_auth_settings.configId()
        ):
            message = self.tr(
                "Please set a username or select an authentication configuration before creating the "
                "project."
            )
            self.pg_auth_settings.setFocus()
        elif (
            self.pg_auth_settings.configId() and not self.pg_use_super_login.isChecked()
        ):
            message = self.tr(
                "Use superuser login for data management tasks when you use an authentication configuration."
            )
            self.pg_use_super_login.setFocus()
        else:
            result = True

        return result, message

    def _pg_service_combo_box_changed(self):

        service = self.pg_service_combo_box.currentData()

        if self._current_service is None:
            self._keep_custom_settings()

        if service:
            service_config = pgserviceparser.service_config(service)

            # QGIS cannot handle manually set hosts with service
            # So it needs to has a host defined in service conf or it takes localhost
            self.pg_host_line_edit.setText(service_config.get("host", "localhost"))

            self.pg_port_line_edit.setText(service_config.get("port", ""))
            self.pg_auth_settings.setUsername(service_config.get("user", ""))
            self.pg_database_line_edit.setText(service_config.get("dbname", ""))
            self.pg_schema_combo_box.setText("")
            self.pg_auth_settings.setPassword(service_config.get("password", ""))
            self.pg_auth_settings.setConfigId("")

            ssl_mode_index = self.pg_ssl_mode_combo_box.findData(
                service_config.get("sslmode", None)
            )
            self.pg_ssl_mode_combo_box.setCurrentIndex(ssl_mode_index)

        else:
            index = self.pg_service_combo_box.findData(
                None, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
            )
            self.pg_host_line_edit.setText(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBHOST
                )
            )
            self.pg_port_line_edit.setText(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPORT
                )
            )
            self.pg_auth_settings.setUsername(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBUSR
                )
            )
            self.pg_database_line_edit.setText(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DATABASE
                )
            )
            self.pg_schema_combo_box.setText(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSCHEMA
                )
            )
            self.pg_auth_settings.setPassword(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPWD
                )
            )
            self.pg_auth_settings.setConfigId(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBAUTHID
                )
            )
            ssl_mode_index = self.pg_ssl_mode_combo_box.findData(
                self.pg_service_combo_box.itemData(
                    index, PgConfigPanel._SERVICE_COMBOBOX_ROLE.SSLMODE
                )
            )
            self.pg_ssl_mode_combo_box.setCurrentIndex(ssl_mode_index)

        self._current_service = service

        self.pg_host_line_edit.setEnabled(
            service is None or not self.pg_host_line_edit.text()
        )
        self.pg_port_line_edit.setEnabled(
            service is None or not self.pg_port_line_edit.text()
        )
        self.pg_database_line_edit.setEnabled(
            service is None or not self.pg_database_line_edit.text()
        )

        self.pg_host_label.setEnabled(
            service is None or not self.pg_host_line_edit.text()
        )
        self.pg_port_label.setEnabled(
            service is None or not self.pg_port_line_edit.text()
        )
        self.pg_database_label.setEnabled(
            service is None or not self.pg_database_line_edit.text()
        )

        self.pg_auth_settings.setEnabled(
            service is None
            or not (
                self.pg_auth_settings.password() and self.pg_auth_settings.username()
            )
        )

        self.pg_ssl_mode_combo_box.setEnabled(
            service is None
            or self.pg_ssl_mode_combo_box.currentIndex()
            == self.pg_ssl_mode_combo_box.findData(None)
        )
        self.pg_ssl_mode_label.setEnabled(
            service is None
            or self.pg_ssl_mode_combo_box.currentIndex()
            == self.pg_ssl_mode_combo_box.findData(None)
        )

    def _keep_custom_settings(self):

        index = self.pg_service_combo_box.findData(
            None, PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_host_line_edit.text().strip(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBHOST,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_port_line_edit.text().strip(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPORT,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_auth_settings.username(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBUSR,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_database_line_edit.text().strip(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DATABASE,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_schema_combo_box.text().strip().lower(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSCHEMA,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_auth_settings.password(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBPWD,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_auth_settings.configId(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBAUTHID,
        )
        self.pg_service_combo_box.setItemData(
            index,
            self.pg_ssl_mode_combo_box.currentData(),
            PgConfigPanel._SERVICE_COMBOBOX_ROLE.SSLMODE,
        )

    def _fill_schema_combo_box(self):
        connection = None
        try:
            connection = psycopg2.connect(
                dbname=self.pg_database_line_edit.text(),
                user=self.pg_auth_settings.username(),
                password=self.pg_auth_settings.password(),
                host=self.pg_host_line_edit.text(),
                port=self.pg_port_line_edit.text(),
            )

        except OperationalError as exception:
            logging.warning(f"Pg connection error: {exception}")
            return

        sql = """SELECT schema_name
        FROM information_schema.schemata; """

        cursor = connection.cursor()
        cursor.execute(sql)

        schemas = cursor.fetchall()

        AUTO_ADDED_SCHEMA = "auto_added_schema"

        currentText = self.pg_schema_combo_box.currentText()

        # Remove all items that were not added by the user
        index_to_remove = self.pg_schema_combo_box.findData(AUTO_ADDED_SCHEMA)
        while index_to_remove > -1:
            self.pg_schema_combo_box.removeItem(index_to_remove)
            index_to_remove = self.pg_schema_combo_box.findData(AUTO_ADDED_SCHEMA)

        for schema in schemas:
            self.pg_schema_combo_box.addItem(schema[0], AUTO_ADDED_SCHEMA)

        currentTextIndex = self.pg_schema_combo_box.findText(currentText)
        if currentTextIndex > -1:
            self.pg_schema_combo_box.setCurrentIndex(currentTextIndex)

        connection.close()
