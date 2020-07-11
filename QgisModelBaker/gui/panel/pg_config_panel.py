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
from qgis.PyQt.QtCore import pyqtSignal

from .db_config_panel import DbConfigPanel
from ...utils import get_ui_class
from QgisModelBaker.utils.qt_utils import (
    Validators,
    NonEmptyStringValidator)
from QgisModelBaker.libili2db.globals import DbActionType

WIDGET_UI = get_ui_class('pg_settings_panel.ui')


class PgConfigPanel(DbConfigPanel, WIDGET_UI):
    """Panel where users fill out connection parameters to Postgres/Postgis database.

    :ivar bool interlis_mode: Value that determines whether the config panel is displayed with messages or fields interlis.
    :cvar notify_fields_modified: Signal that is called when any field is modified.
    :type notify_field_modified: pyqtSignal(str)
    """
    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)
        self.setupUi(self)

        from QgisModelBaker.libili2db.ili2dbconfig import BaseConfiguration
        self.pg_use_super_login.setText(
            self.tr("Execute data management tasks with superuser login from settings ({})").format(BaseConfiguration().super_pg_user))
        self.pg_use_super_login.setToolTip(self.tr("Data management tasks are <ul><li>Create the schema</li><li>Read meta information</li><li>Import data from XTF</li><li>Export data to XTF</li></ul>"))

        if self._db_action_type == DbActionType.GENERATE:
            self.pg_schema_line_edit.setPlaceholderText(self.tr("[Leave empty to create a default schema]"))
        elif self._db_action_type == DbActionType.IMPORT_DATA:
            self.pg_schema_line_edit.setPlaceholderText(self.tr("[Leave empty to import data into a default schema]"))
        elif self._db_action_type == DbActionType.EXPORT:
            self.pg_schema_line_edit.setPlaceholderText(self.tr("[Leave empty to load all schemas in the database]"))

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)

        self.pg_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(
            self.pg_database_line_edit.text())

        self.pg_host_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_port_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_database_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_schema_line_edit.textChanged.connect(self.notify_fields_modified)

    def _show_panel(self):
        if self.interlis_mode:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        else:
            if self._db_action_type == DbActionType.IMPORT_DATA:
                self.pg_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to import data into a default schema]"))
            else:
                self.pg_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to load all schemas in the database]"))

    def get_fields(self, configuration):
        configuration.dbhost = self.pg_host_line_edit.text().strip()
        configuration.dbport = self.pg_port_line_edit.text().strip()
        configuration.dbusr = self.pg_auth_settings.username()
        configuration.database = self.pg_database_line_edit.text().strip()
        configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
        configuration.dbpwd = self.pg_auth_settings.password()
        configuration.dbauthid = self.pg_auth_settings.configId()

        configuration.db_use_super_login = self.pg_use_super_login.isChecked()

    def set_fields(self, configuration):
        self.pg_host_line_edit.setText(configuration.dbhost)
        self.pg_port_line_edit.setText(configuration.dbport)
        self.pg_auth_settings.setUsername(configuration.dbusr)
        self.pg_database_line_edit.setText(configuration.database)
        self.pg_schema_line_edit.setText(configuration.dbschema)
        self.pg_auth_settings.setPassword(configuration.dbpwd)
        self.pg_auth_settings.setConfigId(configuration.dbauthid)

        self.pg_use_super_login.setChecked(configuration.db_use_super_login)

    def is_valid(self):
        result = False
        message = ''
        if not self.pg_host_line_edit.text().strip():
            message = self.tr("Please set a host before creating the project.")
            self.pg_host_line_edit.setFocus()
        elif not self.pg_database_line_edit.text().strip():
            message = self.tr("Please set a database before creating the project.")
            self.pg_database_line_edit.setFocus()
        elif not self.pg_auth_settings.username() and not self.pg_auth_settings.configId():
            message = self.tr("Please set a username or select an authentication configuration before creating the "
                              "project.")
            self.pg_auth_settings.setFocus()
        else:
            result = True

        return result, message
