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

from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.libs.modelbaker.utils.qt_utils import (
    NonEmptyStringValidator,
    Validators,
)
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.db_handling_utils import get_odbc_drivers

from .db_config_panel import DbConfigPanel

WIDGET_UI = gui_utils.get_ui_class("mssql_settings_panel.ui")


class MssqlConfigPanel(DbConfigPanel, WIDGET_UI):

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)
        self.setupUi(self)

        for item_odbc_driver in get_odbc_drivers():
            self.mssql_odbc_driver.addItem(item_odbc_driver)

        # define validators
        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()

        self.mssql_host_line_edit.setValidator(nonEmptyValidator)
        self.mssql_database_line_edit.setValidator(nonEmptyValidator)
        self.mssql_user_line_edit.setValidator(nonEmptyValidator)

        self.mssql_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.mssql_host_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.mssql_database_line_edit.textChanged.emit(
            self.mssql_database_line_edit.text()
        )
        self.mssql_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
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
                self.tr("[Leave empty to create a default schema]")
            )
        else:
            if self._db_action_type == DbActionType.IMPORT_DATA:
                self.mssql_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to import data into a default schema]")
                )
            else:
                self.mssql_schema_line_edit.setPlaceholderText(
                    self.tr("[Leave empty to load all schemas in the database]")
                )

    def get_fields(self, configuration):
        configuration.dbhost = self.mssql_host_line_edit.text().strip()
        configuration.dbinstance = self.mssql_instance_line_edit.text().strip()
        configuration.dbport = self.mssql_port_line_edit.text().strip()
        configuration.dbusr = self.mssql_user_line_edit.text().strip()
        configuration.database = self.mssql_database_line_edit.text().strip()
        configuration.dbschema = self.mssql_schema_line_edit.text().strip().lower()
        configuration.dbpwd = self.mssql_password_line_edit.text()
        configuration.db_odbc_driver = self.mssql_odbc_driver.currentText()

    def set_fields(self, configuration):
        self.mssql_host_line_edit.setText(configuration.dbhost)
        self.mssql_instance_line_edit.setText(configuration.dbinstance)
        self.mssql_port_line_edit.setText(configuration.dbport)
        self.mssql_user_line_edit.setText(configuration.dbusr)
        self.mssql_database_line_edit.setText(configuration.database)
        self.mssql_schema_line_edit.setText(configuration.dbschema)
        self.mssql_password_line_edit.setText(configuration.dbpwd)

        index = self.mssql_odbc_driver.findText(configuration.db_odbc_driver)
        if index != -1:
            self.mssql_odbc_driver.setCurrentIndex(index)

    def is_valid(self):
        result = False
        message = ""
        if not self.mssql_host_line_edit.text().strip():
            message = self.tr("Please set a host before creating the project.")
            self.mssql_host_line_edit.setFocus()
        elif not "{}".format(self.mssql_database_line_edit.text().strip()):
            message = self.tr("Please set a database before creating the project.")
            self.mssql_database_line_edit.setFocus()
        elif not self.mssql_user_line_edit.text().strip():
            message = self.tr("Please set a database user before creating the project.")
            self.mssql_user_line_edit.setFocus()
        elif not self.mssql_odbc_driver.currentText():
            message = self.tr("Please set a odbc driver before creating the project.")
        else:
            result = True

        return result, message
