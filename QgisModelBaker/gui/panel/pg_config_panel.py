# -*- coding: utf-8 -*-
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

from enum import IntEnum

try:
    import QgisModelBaker.libs.pgserviceparser as pgserviceparser
except:
    import pgserviceparser

from qgis.PyQt.QtCore import Qt, pyqtSignal

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

    :ivar bool interlis_mode: Value that determines whether the config panel is displayed with messages or fields interlis.
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

        if self._db_action_type == DbActionType.GENERATE:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]")
            )
        elif self._db_action_type == DbActionType.IMPORT_DATA:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to import data into a default schema]")
            )
        elif self._db_action_type == DbActionType.EXPORT:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to load all schemas in the database]")
            )

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)

        self.pg_host_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.pg_database_line_edit.textChanged.emit(self.pg_database_line_edit.text())

        self.pg_host_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_port_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_database_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_schema_line_edit.textChanged.connect(self.notify_fields_modified)

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

    def _show_panel(self):
        if self.interlis_mode:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]")
            )
        else:
            if self._db_action_type == DbActionType.IMPORT_DATA:
                self.pg_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to import data into a default schema]")
                )
            else:
                self.pg_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to load all schemas in the database]")
                )

    def get_fields(self, configuration):

        configuration.dbservice = self.pg_service_combo_box.currentData()
        configuration.dbhost = self.pg_host_line_edit.text().strip()
        configuration.dbport = self.pg_port_line_edit.text().strip()
        configuration.dbusr = self.pg_auth_settings.username()
        configuration.database = self.pg_database_line_edit.text().strip()
        configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
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
        self.pg_schema_line_edit.setText(configuration.dbschema)
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

        self.pg_host_line_edit.setEnabled(service is None)
        self.pg_port_line_edit.setEnabled(service is None)
        self.pg_database_line_edit.setEnabled(service is None)

        self.pg_host_label.setEnabled(service is None)
        self.pg_port_label.setEnabled(service is None)
        self.pg_database_label.setEnabled(service is None)

        self.pg_auth_settings.setEnabled(service is None)

        self.pg_ssl_mode_combo_box.setEnabled(service is None)
        self.pg_ssl_mode_label.setEnabled(service is None)

        if self._current_service is None:

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
                self.pg_schema_line_edit.text().strip().lower(),
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

        if service:

            service_config = pgserviceparser.service_config(service)

            self.pg_host_line_edit.setText(service_config.get("host", ""))
            self.pg_port_line_edit.setText(service_config.get("port", ""))
            self.pg_auth_settings.setUsername(service_config.get("user", ""))
            self.pg_database_line_edit.setText(service_config.get("dbname", ""))
            self.pg_schema_line_edit.setText("")
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
            self.pg_schema_line_edit.setText(
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
