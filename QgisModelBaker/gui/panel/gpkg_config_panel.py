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
from qgis.PyQt.QtGui import QValidator
from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    make_save_file_selector,
    Validators,
    FileValidator
)

from .db_config_panel import DbConfigPanel
from ...utils import get_ui_class
from QgisModelBaker.libili2db.globals import DbActionType

WIDGET_UI = get_ui_class('gpkg_settings_panel.ui')


class GpkgConfigPanel(DbConfigPanel, WIDGET_UI):
    """Panel where users fill out connection parameters to Geopackage database.

    :ivar bool interlis_mode: Value that determines whether the config panel is displayed with messages or fields interlis.
    :cvar notify_fields_modified: Signal that is called when any field is modified.
    :type notify_field_modified: pyqtSignal(str)
    """
    notify_fields_modified = pyqtSignal(str)

    ValidExtensions = ['gpkg', 'GPKG']

    def __init__(self, parent, db_action_type):
        DbConfigPanel.__init__(self, parent, db_action_type)
        self.setupUi(self)

        # validators
        self.validators = Validators()

        self.gpkgSaveFileValidator = FileValidator(
            pattern=['*.' + ext for ext in self.ValidExtensions], allow_non_existing=True)
        self.gpkgOpenFileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions],
                                                   allow_non_existing=(self._db_action_type == DbActionType.IMPORT_DATA))
        self.gpkg_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)

        self.gpkg_file_line_edit.textChanged.connect(self.notify_fields_modified)

    def _show_panel(self):
        if self.interlis_mode:
            validator = self.gpkgSaveFileValidator
            file_selector = make_save_file_selector(self.gpkg_file_line_edit, title=self.tr("Open GeoPackage database file"),
                                        file_filter=self.tr("GeoPackage Database (*.gpkg *.GPKG)"),
                                                    extensions=['.' + ext for ext in self.ValidExtensions])
        else:
            validator = self.gpkgOpenFileValidator
            file_selector = make_file_selector(self.gpkg_file_line_edit, title=self.tr("Open GeoPackage database file"),
                                        file_filter=self.tr("GeoPackage Database (*.gpkg *.GPKG)"))
        try:
            self.gpkg_file_browse_button.clicked.disconnect()
        except:
            pass

        self.gpkg_file_line_edit.setValidator(validator)
        self.gpkg_file_line_edit.textChanged.emit(self.gpkg_file_line_edit.text())
        self.gpkg_file_browse_button.clicked.connect(file_selector)

    def get_fields(self, configuration):
        configuration.dbfile = self.gpkg_file_line_edit.text().strip()

    def set_fields(self, configuration):
        self.gpkg_file_line_edit.setText(configuration.dbfile)

    def is_valid(self):
        result = False
        message = ''

        db_file = self.gpkg_file_line_edit.text().strip()

        if not db_file or self.gpkg_file_line_edit.validator().validate(db_file, 0)[0] != QValidator.Acceptable:
            message = self.tr("Please set a valid database file before creating the project.")
            self.gpkg_file_line_edit.setFocus()
        else:
            result = True

        return result, message
