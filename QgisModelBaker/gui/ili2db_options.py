# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 03/04/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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

from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    Validators,
    FileValidator
)
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import QSettings
from ..utils import get_ui_class
from qgis.gui import QgsGui

DIALOG_UI = get_ui_class('ili2db_options.ui')


class Ili2dbOptionsDialog(QDialog, DIALOG_UI):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self);
        self.toml_file_key = None

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.disconnect()
        self.buttonBox.rejected.connect(self.rejected)
        self.toml_file_browse_button.clicked.connect(
            make_file_selector(self.toml_file_line_edit, title=self.tr('Open Extra Model Information File (*.toml)'),
                               file_filter=self.tr('Extra Model Info File (*.toml)')))
        self.validators = Validators()
        self.fileValidator = FileValidator(pattern='*.toml', allow_empty=True)
        self.toml_file_line_edit.setValidator(self.fileValidator)

        self.restore_configuration()

        self.toml_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.toml_file_line_edit.textChanged.emit(
            self.toml_file_line_edit.text())

    def accepted(self):
        """ Save settings before accepting the dialog """
        self.save_configuration()
        self.done(1)

    def rejected(self):
        self.restore_configuration()
        self.done(1)

    def create_import_tid(self):
        return self.create_import_tid_checkbox.isChecked()

    def create_basket_col(self):
        return self.create_basket_col_checkbox.isChecked()

    def inheritance_type(self):
        if self.smart1_radio_button.isChecked():
            return 'smart1'
        else:
            return 'smart2'

    def set_toml_file_key(self, key_postfix):
        if key_postfix:
            self.toml_file_key = 'QgsProjectGenerator/ili2db/tomlfile/' + key_postfix
        else:
            self.toml_file_key = None
        self.restore_configuration()

    def toml_file(self):
        return self.toml_file_line_edit.text().strip()

    def stroke_arcs(self):
        return self.stroke_arcs_checkbox.isChecked()

    def save_configuration(self):
        settings = QSettings()
        settings.setValue(
            'QgsProjectGenerator/ili2db/inheritance', self.inheritance_type())
        settings.setValue(
            self.toml_file_key, self.toml_file())
        settings.setValue('QgsProjectGenerator/ili2db/create_basket_col', self.create_basket_col())
        settings.setValue('QgsProjectGenerator/ili2db/create_import_tid', self.create_import_tid())
        settings.setValue('QgsProjectGenerator/ili2db/stroke_arcs', self.stroke_arcs())

    def restore_configuration(self):
        settings = QSettings()
        inheritance = settings.value(
            'QgsProjectGenerator/ili2db/inheritance', 'smart2')
        if inheritance == 'smart1':
            self.smart1_radio_button.setChecked(True)
        else:
            self.smart2_radio_button.setChecked(True)
        create_basket_col = settings.value('QgsProjectGenerator/ili2db/create_basket_col', defaultValue=False, type=bool)
        create_import_tid = settings.value('QgsProjectGenerator/ili2db/create_import_tid', defaultValue=True, type=bool)
        stroke_arcs = settings.value('QgsProjectGenerator/ili2db/stroke_arcs', defaultValue=True, type=bool)

        self.create_basket_col_checkbox.setChecked(create_basket_col)
        self.create_import_tid_checkbox.setChecked(create_import_tid)
        self.stroke_arcs_checkbox.setChecked(stroke_arcs)
        self.toml_file_line_edit.setText(
            settings.value(self.toml_file_key))
