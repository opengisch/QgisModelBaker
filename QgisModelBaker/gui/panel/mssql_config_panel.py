# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    10/05/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania (BSF Swissphoto)
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


class MssqlConfigPanel(DbConfigPanel):

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)

        lbl_host = QLabel(self.tr("Host"))
        lbl_instance = QLabel(self.tr("Instance"))
        lbl_port = QLabel(self.tr("Port"))
        lbl_database = QLabel(self.tr("Database"))
        lbl_schema = QLabel(self.tr("Schema"))
        lbl_user = QLabel(self.tr("User"))
        lbl_password = QLabel(self.tr("Password"))

        self.mssql_host_line_edit = QLineEdit()
        self.mssql_host_line_edit.setPlaceholderText(self.tr("Database Hostname"))
        self.mssql_host_line_edit.setText('localhost')

        self.mssql_instance_line_edit = QLineEdit()
        self.mssql_instance_line_edit.setPlaceholderText(self.tr("[Leave empty to use default instance]"))

        self.mssql_port_line_edit = QLineEdit()
        self.mssql_port_line_edit.setPlaceholderText(self.tr("[Leave empty to use dynamic or standard port 1433]"))

        self.mssql_database_line_edit = QLineEdit()
        self.mssql_database_line_edit.setPlaceholderText(self.tr("Database Name"))

        self.mssql_schema_line_edit = QLineEdit()
        self.mssql_schema_line_edit.setPlaceholderText(self.tr("[Leave empty to load all schemas in the database]"))

        self.mssql_user_line_edit = QLineEdit()
        self.mssql_user_line_edit.setPlaceholderText(self.tr("Database Username"))

        self.mssql_password_line_edit = QLineEdit()
        self.mssql_password_line_edit.setEchoMode(QLineEdit.Password)

        layout = QGridLayout(self)
        layout.addWidget(lbl_host, 0, 0)
        layout.addWidget(lbl_instance, 1, 0)
        layout.addWidget(lbl_port, 2, 0)
        layout.addWidget(lbl_database, 3, 0)
        layout.addWidget(lbl_schema, 4, 0)
        layout.addWidget(lbl_user, 5, 0)
        layout.addWidget(lbl_password, 6, 0)

        layout.addWidget(self.mssql_host_line_edit, 0, 1)
        layout.addWidget(self.mssql_instance_line_edit, 1, 1)
        layout.addWidget(self.mssql_port_line_edit, 2, 1)
        layout.addWidget(self.mssql_database_line_edit, 3, 1)
        layout.addWidget(self.mssql_schema_line_edit, 4, 1)
        layout.addWidget(self.mssql_user_line_edit, 5, 1)
        layout.addWidget(self.mssql_password_line_edit, 6, 1)

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.mssql_host_line_edit.setValidator(nonEmptyValidator)
        self.mssql_database_line_edit.setValidator(nonEmptyValidator)
        self.mssql_user_line_edit.setValidator(nonEmptyValidator)

        self.mssql_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_host_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_database_line_edit.textChanged.emit(
            self.mssql_database_line_edit.text())
        self.mssql_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_user_line_edit.textChanged.emit(self.mssql_user_line_edit.text())

        self.mssql_host_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_instance_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_port_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_database_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_schema_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_user_line_edit.textChanged.connect(self.notify_fields_modified)
        self.mssql_password_line_edit.textChanged.connect(self.notify_fields_modified)

    def _show_panel(self):
        if self.interlis_mode:
            self.mssql_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        else:
            if self._db_action_type == DbActionType.IMPORT_DATA:
                self.mssql_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to import data into a default schema]"))
            else:
                self.mssql_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to load all schemas in the database]"))

    def get_fields(self, configuration):
        configuration.dbhost = self.mssql_host_line_edit.text().strip()
        configuration.dbinstance = self.mssql_instance_line_edit.text().strip()
        configuration.dbport = self.mssql_port_line_edit.text().strip()
        configuration.dbusr = self.mssql_user_line_edit.text().strip()
        configuration.database = self.mssql_database_line_edit.text().strip()
        configuration.dbschema = self.mssql_schema_line_edit.text().strip().lower()
        configuration.dbpwd = self.mssql_password_line_edit.text()

    def set_fields(self, configuration):
        self.mssql_host_line_edit.setText(configuration.dbhost)
        self.mssql_instance_line_edit.setText(configuration.dbinstance)
        self.mssql_port_line_edit.setText(configuration.dbport)
        self.mssql_user_line_edit.setText(configuration.dbusr)
        self.mssql_database_line_edit.setText(configuration.database)
        self.mssql_schema_line_edit.setText(configuration.dbschema)
        self.mssql_password_line_edit.setText(configuration.dbpwd)

    def is_valid(self):
        result = False
        message = ''
        if not self.mssql_host_line_edit.text().strip():
            message = self.tr("Please set a host before creating the project.")
            self.mssql_host_line_edit.setFocus()
        elif not "{}".format(self.mssql_database_line_edit.text().strip()):
            message = self.tr("Please set a database before creating the project.")
            self.mssql_database_line_edit.setFocus()
        elif not self.mssql_user_line_edit.text().strip():
            message = self.tr("Please set a database user before creating the project.")
            self.mssql_user_line_edit.setFocus()
        else:
            result = True

        return result, message
