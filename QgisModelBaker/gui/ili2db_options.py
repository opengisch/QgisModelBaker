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
from qgis.PyQt.QtCore import (
    QSettings,
    Qt
)
from qgis.PyQt.QtGui import QValidator
from qgis.PyQt.QtWidgets import (
    QDialog,
    QSizePolicy
)
from qgis.gui import (
    QgsGui,
    QgsMessageBar
)

from QgisModelBaker.utils import get_ui_class
from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    Validators,
    FileValidator
)

DIALOG_UI = get_ui_class('ili2db_options.ui')


class Ili2dbOptionsDialog(QDialog, DIALOG_UI):

    ValidExtensions = ['toml', 'TOML']
    SQLValidExtensions = ['sql', 'SQL']

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
                               file_filter=self.tr('Extra Model Info File (*.toml *.TOML)')))
        self.pre_script_file_browse_button.clicked.connect(
            make_file_selector(self.pre_script_file_line_edit, title=self.tr('SQL script to run before (*.sql)'),
                               file_filter=self.tr('SQL script to run before (*.sql *.SQL)')))
        self.post_script_file_browse_button.clicked.connect(
            make_file_selector(self.post_script_file_line_edit, title=self.tr('SQL script to run after (*.sql)'),
                               file_filter=self.tr('SQL script to run after (*.sql *.SQL)')))

        self.validators = Validators()
        self.file_validator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_empty=True)
        self.toml_file_line_edit.setValidator(self.file_validator)

        self.sql_file_validator = FileValidator(pattern=['*.' + ext for ext in self.SQLValidExtensions], allow_empty=True)
        self.pre_script_file_line_edit.setValidator(self.sql_file_validator)
        self.post_script_file_line_edit.setValidator(self.sql_file_validator)

        self.restore_configuration()

        self.toml_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.toml_file_line_edit.textChanged.emit(self.toml_file_line_edit.text())
        self.pre_script_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pre_script_file_line_edit.textChanged.emit(self.pre_script_file_line_edit.text())
        self.post_script_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.post_script_file_line_edit.textChanged.emit(self.post_script_file_line_edit.text())

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

    def accepted(self):
        """ Save settings before accepting the dialog """
        for line_edit in [self.pre_script_file_line_edit, self.post_script_file_line_edit, self.toml_file_line_edit]:
            if line_edit.validator().validate(line_edit.text().strip(), 0)[0] != QValidator.Acceptable:
                self.bar.pushWarning(self.tr("Warning"), self.tr("Please fix the '{}' value before saving the options.").format(
                    line_edit.objectName().split("_file_line_edit")[0].replace("_", " ")))
                return

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
            self.toml_file_key = 'QgisModelBaker/ili2db/tomlfile/' + key_postfix
        else:
            self.toml_file_key = None
        self.restore_configuration()

    def toml_file(self):
        return self.toml_file_line_edit.text().strip()

    def pre_script(self):
        return self.pre_script_file_line_edit.text().strip()

    def post_script(self):
        return self.post_script_file_line_edit.text().strip()

    def stroke_arcs(self):
        return self.stroke_arcs_checkbox.isChecked()

    def save_configuration(self):
        settings = QSettings()
        settings.setValue(
            'QgisModelBaker/ili2db/inheritance', self.inheritance_type())
        settings.setValue(
            self.toml_file_key, self.toml_file())
        settings.setValue('QgisModelBaker/ili2db/create_basket_col', self.create_basket_col())
        settings.setValue('QgisModelBaker/ili2db/create_import_tid', self.create_import_tid())
        settings.setValue('QgisModelBaker/ili2db/stroke_arcs', self.stroke_arcs())

    def restore_configuration(self):
        settings = QSettings()
        inheritance = settings.value(
            'QgisModelBaker/ili2db/inheritance', 'smart2')
        if inheritance == 'smart1':
            self.smart1_radio_button.setChecked(True)
        else:
            self.smart2_radio_button.setChecked(True)
        create_basket_col = settings.value('QgisModelBaker/ili2db/create_basket_col', defaultValue=False, type=bool)
        create_import_tid = settings.value('QgisModelBaker/ili2db/create_import_tid', defaultValue=True, type=bool)
        stroke_arcs = settings.value('QgisModelBaker/ili2db/stroke_arcs', defaultValue=True, type=bool)

        self.create_basket_col_checkbox.setChecked(create_basket_col)
        self.create_import_tid_checkbox.setChecked(create_import_tid)
        self.stroke_arcs_checkbox.setChecked(stroke_arcs)
        self.toml_file_line_edit.setText(
            settings.value(self.toml_file_key))
