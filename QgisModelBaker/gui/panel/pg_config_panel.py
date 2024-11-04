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

from qgis.PyQt.QtCore import QSettings, Qt, QThread, QTimer

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    BaseConfiguration,
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.utils import gui_utils

from ...utils.globals import AdministrativeDBActionTypes
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

    REFRESH_SCHEMAS_TIMEOUT_MS = 500

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)
        self.setupUi(self)

        self._current_service = None

        self._fill_schema_combo_box_timer = QTimer()
        self._fill_schema_combo_box_timer.setSingleShot(True)
        self._fill_schema_combo_box_timer.timeout.connect(self._fill_schema_combo_box)

        self._read_pg_schemas_task = ReadPgSchemasTask(self)
        self._read_pg_schemas_task.finished.connect(self._read_pg_schemas_task_finished)

        self.base_config = BaseConfiguration()
        settings = QSettings()
        settings.beginGroup("QgisModelBaker/ili2db")
        self.base_config.restore(settings)

        self.pg_use_super_login.setText(
            self.tr(
                "Execute data management tasks with superuser login from settings ({})"
            ).format(self.base_config.super_pg_user)
        )

        self.pg_use_super_login.setToolTip(
            self.tr(
                "Data management tasks are <ul><li>Create the schema</li><li>Read meta information</li><li>Import data from XTF</li></ul>"
            )
        )

        # define validators
        self.validators = gui_utils.Validators()
        nonEmptyValidator = gui_utils.NonEmptyStringValidator()

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

        self.pg_host_line_edit.textChanged.connect(self._fields_modified)
        self.pg_port_line_edit.textChanged.connect(self._fields_modified)
        self.pg_database_line_edit.textChanged.connect(self._fields_modified)
        self.pg_schema_combo_box.currentTextChanged.connect(self.notify_fields_modified)

        self.pg_auth_settings.usernameChanged.connect(self._fields_modified)
        self.pg_auth_settings.passwordChanged.connect(self._fields_modified)
        self.pg_auth_settings.configIdChanged.connect(self._fields_modified)

        self.pg_use_super_login.stateChanged.connect(self._fields_modified)

        # Fill pg_services combo box
        self.pg_service_combo_box.addItem(self.tr("None"), None)
        services, _ = db_utils.get_service_names()
        for service in services:
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

    def __del__(self):
        # Make sure the refresh schemas task is finished to avoid crashes
        try:
            if self._read_pg_schemas_task:
                self._read_pg_schemas_task.wait()
        except RuntimeError:
            pass

    def _show_panel(self):

        self._fill_schema_combo_box()

        if (
            self._db_action_type == DbActionType.GENERATE
            or self._db_action_type == DbActionType.IMPORT_DATA
        ):
            self.pg_schema_combo_box.lineEdit().setPlaceholderText(
                self.tr("Schema Name")
            )
        elif self._db_action_type == DbActionType.EXPORT:
            self.pg_schema_combo_box.lineEdit().setPlaceholderText(
                self.tr("[Enter a valid schema]")
            )
            self.pg_use_super_login.setVisible(False)
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

        service_config, error = db_utils.get_service_config(configuration.dbservice)
        if error:
            logging.warning(error)

        # if no dbservice in the configuration or one is there but the servicefile is not available anymore
        if not service_config:

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
        else:
            index = self.pg_service_combo_box.findData(configuration.dbservice)
            self.pg_service_combo_box.setCurrentIndex(index)

            # Only apply stored QSettings if the
            # PG service didn't have a value for them
            if not service_config.get("host"):
                self.pg_host_line_edit.setText(configuration.dbhost)

            if not service_config.get("port"):
                self.pg_port_line_edit.setText(configuration.dbport)

            if not service_config.get("dbname"):
                self.pg_database_line_edit.setText(configuration.database)

            if not service_config.get("user"):
                self.pg_auth_settings.setUsername(configuration.dbusr)

            if not service_config.get("password"):
                self.pg_auth_settings.setPassword(configuration.dbpwd)

            if not service_config.get("sslmode"):
                index = self.pg_ssl_mode_combo_box.findData(configuration.sslmode)
                self.pg_ssl_mode_combo_box.setCurrentIndex(index)

            # On the contrary, next settings will never be stored
            # in PG service, so always take them from QSettings
            self.pg_schema_combo_box.setCurrentText(configuration.dbschema)
            self.pg_auth_settings.setConfigId(configuration.dbauthid)
            self.pg_use_super_login.setChecked(configuration.db_use_super_login)

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
            self.pg_auth_settings.configId()
            and not self.pg_use_super_login.isChecked()
            and self._db_action_type
            in {item.value for item in AdministrativeDBActionTypes}
        ):
            # For Python v3.12+, we can just check like this: self._db_action_type in AdministrativeDBActionTypes
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

        service_config, error = db_utils.get_service_config(service)
        if error:
            logging.warning(error)

        if service_config:
            # QGIS cannot handle manually set hosts with service
            # So it needs to have a host defined in service conf or it takes localhost
            self.pg_host_line_edit.setText(service_config.get("host", "localhost"))

            self.pg_port_line_edit.setText(service_config.get("port", ""))
            self.pg_auth_settings.setUsername(service_config.get("user", ""))
            self.pg_database_line_edit.setText(service_config.get("dbname", ""))
            self.pg_schema_combo_box.setCurrentText("")
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
            self.pg_schema_combo_box.setCurrentText(
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

        self._fields_modified()

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
            self.pg_schema_combo_box.currentText().strip().lower(),
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

    def _fields_modified(self):
        self._fill_schema_combo_box_timer.start(self.REFRESH_SCHEMAS_TIMEOUT_MS)

        self.notify_fields_modified.emit()

    def _fill_schema_combo_box(self):

        if self._read_pg_schemas_task.isRunning():
            self._fill_schema_combo_box_timer.start()
            return

        configuration = Ili2DbCommandConfiguration()
        configuration.base_configuration = self.base_config
        self.get_fields(configuration)
        configuration.tool = DbIliMode.pg

        self._read_pg_schemas_task.configuration_changed(configuration)

    def _read_pg_schemas_task_finished(self):
        schemas = self._read_pg_schemas_task.schemas

        AUTO_ADDED_SCHEMA = "auto_added_schema"

        currentText = self.pg_schema_combo_box.currentText()

        # Remove all items that were not added by the user
        index_to_remove = self.pg_schema_combo_box.findData(AUTO_ADDED_SCHEMA)
        while index_to_remove > -1:
            self.pg_schema_combo_box.removeItem(index_to_remove)
            index_to_remove = self.pg_schema_combo_box.findData(AUTO_ADDED_SCHEMA)

        for schema in schemas:
            self.pg_schema_combo_box.addItem(schema, AUTO_ADDED_SCHEMA)

        currentTextIndex = self.pg_schema_combo_box.findText(currentText)
        if currentTextIndex > -1:
            self.pg_schema_combo_box.setCurrentIndex(currentTextIndex)


class ReadPgSchemasTask(QThread):
    def __init__(self, parent):
        super().__init__(parent)

        self.schemas = []
        self._configuration = None

    def configuration_changed(self, configuration):
        self._configuration = configuration
        self.start()

    def run(self):

        try:
            db_connector = db_utils.get_db_connector(self._configuration)
            if not db_connector:
                logging.warning("Refresh schema list connection error")
                self.schemas = []
                return

            self.schemas = db_connector.get_schemas()

        except Exception as exception:
            logging.warning(f"Refresh schema list error: {exception}")
            self.schemas = []
