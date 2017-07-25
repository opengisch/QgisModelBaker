# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 6.6.2017
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

from projectgenerator.utils import get_ui_class
from projectgenerator.utils import qt_utils
from qgis.PyQt.QtWidgets import QDialog

from projectgenerator.utils.qt_utils import FileValidator, Validators

DIALOG_UI = get_ui_class('options.ui')

class OptionsDialog(QDialog, DIALOG_UI):
    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        self.custom_model_directories_line_edit.setText(configuration.custom_model_directories)
        self.custom_model_directories_box.setChecked(configuration.custom_model_directories_enabled)
        self.java_path_line_edit.setText(configuration.java_path)
        self.java_path_search_button.clicked.connect(qt_utils.make_file_selector(self.java_path_line_edit, self.tr('Select java application.'), self.tr('java (*)')))
        self.java_path_line_edit.setValidator(FileValidator(is_executable=True, allow_empty=True))
        self.validators = Validators()
        self.java_path_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.buttonBox.accepted.connect(self.accepted)

    def accepted(self):
        self.configuration.custom_model_directories = self.custom_model_directories_line_edit.text()
        self.configuration.custom_model_directories_enabled = self.custom_model_directories_box.isChecked()
        self.configuration.java_path = self.java_path_line_edit.text().strip()
