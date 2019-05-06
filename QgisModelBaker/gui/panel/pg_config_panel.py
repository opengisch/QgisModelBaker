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
from qgis.PyQt.QtWidgets import (QLabel,
                                 QGridLayout,
                                 QLineEdit,
                                 QCheckBox)

from .db_config_panel import DbConfigPanel
from QgisModelBaker.utils.qt_utils import (
    Validators,
    NonEmptyStringValidator)
from QgisModelBaker.libili2db.globals import DbActionType


class PgConfigPanel(DbConfigPanel):

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)

        lbl_host = QLabel(self.tr("Host"))
        lbl_port = QLabel(self.tr("Port"))
        lbl_database = QLabel(self.tr("Database"))
        lbl_schema = QLabel(self.tr("Schema"))
        lbl_user = QLabel(self.tr("User"))
        lbl_password = QLabel(self.tr("Password"))

        self.pg_host_line_edit = QLineEdit()
        self.pg_host_line_edit.setPlaceholderText(self.tr("Database Hostname"))
        self.pg_host_line_edit.setText('localhost')

        self.pg_port_line_edit = QLineEdit()
        self.pg_port_line_edit.setPlaceholderText(self.tr("[Leave empty to use standard port 5432]"))

        self.pg_database_line_edit = QLineEdit()
        self.pg_database_line_edit.setPlaceholderText(self.tr("Database Name"))

        self.pg_schema_line_edit = QLineEdit()
        self.pg_schema_line_edit.setPlaceholderText(self.tr("[Leave empty to load all schemas in the database]"))

        self.pg_user_line_edit = QLineEdit()
        self.pg_user_line_edit.setPlaceholderText(self.tr("Database Username"))

        self.pg_password_line_edit = QLineEdit()
        self.pg_password_line_edit.setEchoMode(QLineEdit.Password)
        self.pg_password_line_edit.setPlaceholderText(self.tr("[Leave empty to use system password]"))

        from QgisModelBaker.libili2db.ili2dbconfig import BaseConfiguration

        if self._db_action_type != DbActionType.EXPORT:
            self.pg_use_super_login = QCheckBox()
            self.pg_use_super_login.setText(
                self.tr("Generate schema with superuser login from settings ({})").format(BaseConfiguration().super_pg_user))

        layout = QGridLayout(self)
        layout.addWidget(lbl_host, 0, 0)
        layout.addWidget(lbl_port, 1, 0)
        layout.addWidget(lbl_database, 2, 0)
        layout.addWidget(lbl_schema, 3, 0)
        layout.addWidget(lbl_user, 4, 0)
        layout.addWidget(lbl_password, 5, 0)

        layout.addWidget(self.pg_host_line_edit, 0, 1)
        layout.addWidget(self.pg_port_line_edit, 1, 1)
        layout.addWidget(self.pg_database_line_edit, 2, 1)
        layout.addWidget(self.pg_schema_line_edit, 3, 1)
        layout.addWidget(self.pg_user_line_edit, 4, 1)
        layout.addWidget(self.pg_password_line_edit, 5, 1)

        if self._db_action_type != DbActionType.EXPORT:
            layout.addWidget(self.pg_use_super_login,6,1)

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)
        self.pg_user_line_edit.setValidator(nonEmptyValidator)

        self.pg_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(
            self.pg_database_line_edit.text())
        self.pg_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_user_line_edit.textChanged.emit(self.pg_user_line_edit.text())

        self.pg_host_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_port_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_database_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_schema_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_user_line_edit.textChanged.connect(self.notify_fields_modified)
        self.pg_password_line_edit.textChanged.connect(self.notify_fields_modified)

    def _show_panel(self):
        if self.interlis_mode:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        else:
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to load all schemas in the database]"))

    def get_fields(self, configuration):
        configuration.dbhost = self.pg_host_line_edit.text().strip()
        configuration.dbport = self.pg_port_line_edit.text().strip()
        configuration.dbusr = self.pg_user_line_edit.text().strip()
        configuration.database = "'{}'".format(self.pg_database_line_edit.text().strip())
        configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
        configuration.dbpwd = self.pg_password_line_edit.text()

        if self._db_action_type != DbActionType.EXPORT:
            configuration.db_use_super_login = self.pg_use_super_login.isChecked()

    def set_fields(self, configuration):
        self.pg_host_line_edit.setText(configuration.dbhost)
        self.pg_port_line_edit.setText(configuration.dbport)
        self.pg_user_line_edit.setText(configuration.dbusr)
        self.pg_database_line_edit.setText(configuration.database)
        self.pg_schema_line_edit.setText(configuration.dbschema)
        self.pg_password_line_edit.setText(configuration.dbpwd)

        if self._db_action_type != DbActionType.EXPORT:
            self.pg_use_super_login.setChecked(configuration.db_use_super_login)

    def is_valid(self):
        result = False
        message = ''
        if not self.pg_host_line_edit.text().strip():
            message = self.tr("Please set a host before creating the project.")
            self.pg_host_line_edit.setFocus()
        elif not "{}".format(self.pg_database_line_edit.text().strip()):
            message = self.tr("Please set a database before creating the project.")
            self.pg_database_line_edit.setFocus()
        elif not self.pg_user_line_edit.text().strip():
            message = self.tr("Please set a database user before creating the project.")
            self.pg_user_line_edit.setFocus()
        else:
            result = True

        return result, message
