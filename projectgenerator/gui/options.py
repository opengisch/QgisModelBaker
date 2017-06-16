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

DIALOG_UI = get_ui_class('options.ui')

class OptionsDialog(QDialog, DIALOG_UI):
    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        self.custom_model_directories_line_edit.setText(configuration.custom_model_directories)
        self.custom_model_directories_box.setChecked(configuration.custom_model_directories_enabled)
        self.buttonBox.accepted.connect(self.accepted)

    def accepted(self):
        self.configuration.custom_model_directories = self.custom_model_directories_line_edit.text()
        self.configuration.custom_model_directories_enabled = self.custom_model_directories_box.isChecked()